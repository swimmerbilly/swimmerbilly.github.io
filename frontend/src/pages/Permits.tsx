import { useMemo, useState } from "react";
import { api } from "../api/client";
import { EmptyState, PageHeader, useAsyncData } from "../components/ui";
import type { BuildingPermit, Jurisdiction, MarketFirmRow } from "../types";

function money(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  });
}

export default function PermitsPage() {
  const [jurisdictionId, setJurisdictionId] = useState("");
  const [months, setMonths] = useState(24);
  const [structuralOnly, setStructuralOnly] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedContractor, setSelectedContractor] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);

  const { data: jurisdictions } = useAsyncData(() => api.getPermitJurisdictions());
  const { data: stats, reload: reloadStats } = useAsyncData(() => api.getPermitStats());
  const {
    data: report,
    loading,
    error,
    reload,
  } = useAsyncData(
    () =>
      api.getMarketResearch({
        jurisdictionId: jurisdictionId || undefined,
        months,
        structuralOnly,
        q: query || undefined,
      }),
    [jurisdictionId, months, structuralOnly, query]
  );

  const {
    data: permits,
    reload: reloadPermits,
  } = useAsyncData(
    () =>
      api.getPermits({
        jurisdictionId: jurisdictionId || undefined,
        structuralOnly,
        contractor: selectedContractor || undefined,
        q: selectedContractor ? undefined : query || undefined,
        limit: 80,
      }),
    [jurisdictionId, structuralOnly, selectedContractor, query]
  );

  const jurisdictionName = useMemo(() => {
    const map = new Map((jurisdictions ?? []).map((j: Jurisdiction) => [j.id, j.name]));
    return (id: string) => map.get(id) ?? id;
  }, [jurisdictions]);

  const refresh = () => {
    reload();
    reloadStats();
    reloadPermits();
  };

  const handleSyncMarket = async () => {
    setSyncing(true);
    setSyncError(null);
    setSyncMessage(null);
    try {
      const runs = await api.syncPermits(2000);
      const lines = runs.map(
        (run) =>
          `${run.jurisdiction_id}: ${run.status} — ${run.message ?? `${run.records_upserted} saved`}`
      );
      setSyncMessage(lines.join(" · "));
      refresh();
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setSyncing(false);
    }
  };

  const handleSeed = async () => {
    setSyncing(true);
    setSyncError(null);
    try {
      const result = await api.seedSamplePermits();
      setSyncMessage(
        `Loaded sample market rows (${result.created} new / ${result.updated} updated).`
      );
      refresh();
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Could not load samples");
    } finally {
      setSyncing(false);
    }
  };

  const renderFirmTable = (
    title: string,
    rows: MarketFirmRow[] | undefined,
    mode: "contractor" | "architect" | "engineer"
  ) => (
    <div className="card market-panel">
      <h3>{title}</h3>
      {!rows?.length ? (
        <p className="meta">No rows yet for this window.</p>
      ) : (
        <div className="market-table-wrap">
          <table className="market-table">
            <thead>
              <tr>
                <th>{mode === "contractor" ? "Contractor" : mode === "architect" ? "Architect" : "Engineer"}</th>
                <th>Jobs</th>
                <th>Win $</th>
                {mode === "contractor" && <th>Avg job</th>}
                <th>/mo</th>
                <th>Partners</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={row.name}
                  className={
                    mode === "contractor" && selectedContractor === row.name ? "is-selected" : undefined
                  }
                  onClick={() => {
                    if (mode === "contractor") {
                      setSelectedContractor((prev) => (prev === row.name ? null : row.name));
                    }
                  }}
                >
                  <td>
                    <strong>{row.name}</strong>
                    {row.firm && row.firm !== row.name ? <div className="meta">{row.firm}</div> : null}
                  </td>
                  <td>{row.job_count}</td>
                  <td>{money(row.total_value)}</td>
                  {mode === "contractor" && <td>{money(row.avg_job_value)}</td>}
                  <td>{row.jobs_per_month.toFixed(1)}</td>
                  <td className="market-partners">
                    {(mode === "contractor"
                      ? [...(row.top_architects ?? []), ...(row.top_engineers ?? [])]
                      : mode === "architect"
                        ? [...(row.top_contractors ?? []), ...(row.top_engineers ?? [])]
                        : [...(row.top_contractors ?? []), ...(row.top_architects ?? [])]
                    )
                      .slice(0, 4)
                      .join(" · ") || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  return (
    <>
      <PageHeader
        title="Market Research"
        description="Public permit intelligence for Boulder County — who is winning work, for how much, how often, and which architects / structural engineers show up with them."
      />

      <div className="card permit-intro">
        <p>
          Best public signal today: <strong>City of Boulder open data</strong> (contractor + estimated
          project cost on ~building permits). Architect and structural engineer of record are thinner
          in bulk feeds — they usually live on Accela detail pages or plan stamps. Sync open data for
          volume; use samples or import when you have SE/architect names.
        </p>
        <div className="permit-actions">
          <button className="btn btn-primary" onClick={handleSyncMarket} disabled={syncing}>
            {syncing ? "Syncing…" : "Sync public permit data"}
          </button>
          <button className="btn btn-ghost" onClick={handleSeed} disabled={syncing}>
            Load sample market data
          </button>
        </div>
        {syncError && <div className="error-banner">{syncError}</div>}
        {syncMessage && <p className="sync-result">{syncMessage}</p>}
      </div>

      {(stats || report) && (
        <div className="stats-grid permit-stats">
          <div className="stat-card">
            <div className="label">Permits in window</div>
            <div className="value">{report?.permit_count ?? stats?.total ?? 0}</div>
          </div>
          <div className="stat-card">
            <div className="label">Estimated win volume</div>
            <div className="value">{money(report?.total_estimated_value ?? stats?.total_estimated_value)}</div>
          </div>
          <div className="stat-card">
            <div className="label">Contractor coverage</div>
            <div className="value">{report ? `${report.coverage.contractor_pct}%` : "—"}</div>
          </div>
          <div className="stat-card">
            <div className="label">Architect / SE coverage</div>
            <div className="value">
              {report
                ? `${report.coverage.architect_pct}% / ${report.coverage.engineer_pct}%`
                : "—"}
            </div>
          </div>
        </div>
      )}

      <div className="card permit-filters">
        <div className="permit-filter-row">
          <label>
            Jurisdiction
            <select value={jurisdictionId} onChange={(e) => setJurisdictionId(e.target.value)}>
              <option value="">All tracked</option>
              {(jurisdictions ?? []).map((j) => (
                <option key={j.id} value={j.id}>
                  {j.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Window
            <select value={months} onChange={(e) => setMonths(Number(e.target.value))}>
              <option value={12}>Last 12 months</option>
              <option value={24}>Last 24 months</option>
              <option value={36}>Last 36 months</option>
              <option value={60}>Last 5 years</option>
            </select>
          </label>
          <label>
            Search firms / people
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Contractor, architect, engineer…"
            />
          </label>
          <label className="permit-checkbox">
            <input
              type="checkbox"
              checked={structuralOnly}
              onChange={(e) => setStructuralOnly(e.target.checked)}
            />
            Structural-leaning only
          </label>
        </div>
        {selectedContractor && (
          <p className="meta">
            Filtering permits for <strong>{selectedContractor}</strong>{" "}
            <button className="btn btn-ghost btn-sm" onClick={() => setSelectedContractor(null)}>
              Clear
            </button>
          </p>
        )}
      </div>

      {loading && <p className="meta">Building market view…</p>}
      {error && <div className="error-banner">{error}</div>}

      {!loading && report && report.permit_count === 0 && (
        <EmptyState
          message="No permit market data yet. Sync City of Boulder open data or load samples."
          action={
            <button className="btn btn-primary" onClick={handleSyncMarket} disabled={syncing}>
              Sync public permit data
            </button>
          }
        />
      )}

      {report && report.permit_count > 0 && (
        <div className="market-grid">
          {renderFirmTable("Who’s winning (contractors)", report.contractors, "contractor")}
          {renderFirmTable("Architects on those jobs", report.architects, "architect")}
          {renderFirmTable("Structural engineers", report.engineers, "engineer")}
        </div>
      )}

      {report && report.contractor_architect_pairs.length > 0 && (
        <div className="card market-panel">
          <h3>Frequent contractor ↔ architect pairings</h3>
          <div className="market-table-wrap">
            <table className="market-table">
              <thead>
                <tr>
                  <th>Contractor</th>
                  <th>Architect</th>
                  <th>Jobs</th>
                  <th>Combined $</th>
                </tr>
              </thead>
              <tbody>
                {report.contractor_architect_pairs.map((pair) => (
                  <tr key={`${pair.contractor}-${pair.architect}`}>
                    <td>{pair.contractor}</td>
                    <td>{pair.architect}</td>
                    <td>{pair.job_count}</td>
                    <td>{money(pair.total_value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {report?.notes?.length ? (
        <div className="card market-notes">
          <h3>Data reality check</h3>
          <ul>
            {report.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="card market-panel">
        <h3>Recent permits {selectedContractor ? `· ${selectedContractor}` : ""}</h3>
        {!permits?.length ? (
          <p className="meta">No permit rows for this filter.</p>
        ) : (
          <div className="list">
            {permits.map((permit: BuildingPermit) => (
              <div key={permit.id} className="list-item">
                <div>
                  <div className="list-item-title">
                    {permit.permit_number}
                    {permit.has_structural_plans && <span className="badge">Structural</span>}
                    {permit.status && <span className="badge badge-code">{permit.status}</span>}
                  </div>
                  <p className="meta">
                    {jurisdictionName(permit.jurisdiction_id)}
                    {permit.permit_type ? ` · ${permit.permit_type}` : ""}
                    {permit.estimated_value_amount != null
                      ? ` · ${money(permit.estimated_value_amount)}`
                      : ""}
                  </p>
                  {(permit.address || permit.city) && (
                    <p className="meta">{[permit.address, permit.city].filter(Boolean).join(", ")}</p>
                  )}
                  <p className="permit-engineer">
                    {permit.contractor_name ? (
                      <>
                        Contractor: <strong>{permit.contractor_name}</strong>
                      </>
                    ) : (
                      "Contractor: —"
                    )}
                    {(permit.architect_firm || permit.architect_name) && (
                      <>
                        {" · "}Architect:{" "}
                        <strong>{permit.architect_firm || permit.architect_name}</strong>
                      </>
                    )}
                    {(permit.structural_engineer_name || permit.structural_engineer_firm) && (
                      <>
                        {" · "}SE:{" "}
                        <strong>
                          {permit.structural_engineer_name || permit.structural_engineer_firm}
                        </strong>
                        {permit.structural_engineer_firm && permit.structural_engineer_name
                          ? ` (${permit.structural_engineer_firm})`
                          : ""}
                      </>
                    )}
                  </p>
                  {permit.description && <p style={{ marginTop: "0.5rem" }}>{permit.description}</p>}
                  {permit.source_url && (
                    <p style={{ marginTop: "0.5rem" }}>
                      <a
                        className="btn btn-ghost btn-sm"
                        href={permit.source_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Source
                      </a>
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
