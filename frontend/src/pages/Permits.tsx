import { useMemo, useState } from "react";
import { api } from "../api/client";
import { EmptyState, PageHeader, useAsyncData } from "../components/ui";
import type { BuildingPermit, Jurisdiction } from "../types";

export default function PermitsPage() {
  const [jurisdictionId, setJurisdictionId] = useState("");
  const [structuralOnly, setStructuralOnly] = useState(true);
  const [engineer, setEngineer] = useState("");
  const [query, setQuery] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);

  const { data: jurisdictions } = useAsyncData(() => api.getPermitJurisdictions());
  const { data: stats, reload: reloadStats } = useAsyncData(() => api.getPermitStats());
  const {
    data: permits,
    loading,
    error,
    reload,
  } = useAsyncData(
    () =>
      api.getPermits({
        jurisdictionId: jurisdictionId || undefined,
        structuralOnly,
        engineer: engineer || undefined,
        q: query || undefined,
      }),
    [jurisdictionId, structuralOnly, engineer, query]
  );

  const jurisdictionName = useMemo(() => {
    const map = new Map((jurisdictions ?? []).map((j: Jurisdiction) => [j.id, j.name]));
    return (id: string) => map.get(id) ?? id;
  }, [jurisdictions]);

  const refresh = () => {
    reload();
    reloadStats();
  };

  const handleSyncAll = async () => {
    setSyncing(true);
    setSyncError(null);
    setSyncMessage(null);
    try {
      const runs = await api.syncPermits();
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
        `Loaded sample permits (${result.created} new / ${result.updated} updated, ${result.structural_found} structural).`
      );
      refresh();
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Could not load samples");
    } finally {
      setSyncing(false);
    }
  };

  const handleSyncOne = async (id: string) => {
    setSyncing(true);
    setSyncError(null);
    try {
      const run = await api.syncPermitJurisdiction(id);
      setSyncMessage(`${run.jurisdiction_id}: ${run.status} — ${run.message ?? "done"}`);
      refresh();
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Building Permits"
        description="Boulder County + surrounding cities — find permits with structural plans and the structural engineer of record."
      />

      <div className="card permit-intro">
        <p>
          This watches public permit portals across Boulder County jurisdictions. Accela cities
          (County + Longmont) can be crawled automatically. City of Boulder / Louisville (EnerGov)
          and smaller towns are listed with portal links — import key records or expand crawlers later.
        </p>
        <div className="permit-actions">
          <button className="btn btn-primary" onClick={handleSyncAll} disabled={syncing}>
            {syncing ? "Working…" : "Crawl Accela jurisdictions"}
          </button>
          <button className="btn btn-ghost" onClick={handleSeed} disabled={syncing}>
            Load sample permits
          </button>
        </div>
        {syncError && <div className="error-banner">{syncError}</div>}
        {syncMessage && <p className="sync-result">{syncMessage}</p>}
      </div>

      {stats && (
        <div className="stats-grid permit-stats">
          <div className="stat-card">
            <div className="label">Permits tracked</div>
            <div className="value">{stats.total}</div>
          </div>
          <div className="stat-card">
            <div className="label">With structural plans</div>
            <div className="value">{stats.with_structural_plans}</div>
          </div>
          <div className="stat-card">
            <div className="label">Engineer named</div>
            <div className="value">{stats.with_engineer_named}</div>
          </div>
        </div>
      )}

      <div className="card permit-filters">
        <div className="permit-filter-row">
          <label>
            Jurisdiction
            <select value={jurisdictionId} onChange={(e) => setJurisdictionId(e.target.value)}>
              <option value="">All</option>
              {jurisdictions?.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Engineer
            <input
              value={engineer}
              onChange={(e) => setEngineer(e.target.value)}
              placeholder="Name contains…"
            />
          </label>
          <label>
            Search
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Address, permit #, type…"
            />
          </label>
          <label className="permit-checkbox">
            <input
              type="checkbox"
              checked={structuralOnly}
              onChange={(e) => setStructuralOnly(e.target.checked)}
            />
            Structural plans only
          </label>
        </div>
      </div>

      {jurisdictions && jurisdictions.length > 0 && (
        <>
          <h3 className="section-title">Jurisdictions</h3>
          <div className="list permit-jurisdiction-list">
            {jurisdictions.map((j) => (
              <div key={j.id} className="list-item">
                <div>
                  <div className="title">
                    {j.name}
                    <span className="badge badge-code">{j.system}</span>
                    {j.crawlable ? (
                      <span className="badge badge-active">Crawlable</span>
                    ) : (
                      <span className="badge badge-on_hold">Portal link</span>
                    )}
                  </div>
                  <p className="meta">{j.notes}</p>
                  <div className="comm-actions">
                    {(j.search_url || j.portal_url) && (
                      <a
                        className="btn btn-ghost btn-sm"
                        href={j.search_url || j.portal_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Open portal
                      </a>
                    )}
                    {j.crawlable && (
                      <button
                        className="btn btn-ghost btn-sm"
                        onClick={() => handleSyncOne(j.id)}
                        disabled={syncing}
                      >
                        Crawl now
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <h3 className="section-title">Results</h3>
      {error && <div className="error-banner">{error}</div>}
      {loading && <p className="meta">Loading permits…</p>}
      {!loading && permits?.length === 0 && (
        <EmptyState
          message="No permits match yet. Load samples or crawl Accela jurisdictions to get started."
          action={
            <button className="btn btn-primary" onClick={handleSeed} disabled={syncing}>
              Load sample permits
            </button>
          }
        />
      )}

      <div className="list">
        {permits?.map((permit: BuildingPermit) => (
          <div key={permit.id} className="list-item">
            <div>
              <div className="title">
                {permit.permit_number}
                {permit.has_structural_plans && (
                  <span className="badge badge-priority badge-priority-high">Structural</span>
                )}
                {permit.status && <span className="badge badge-code">{permit.status}</span>}
              </div>
              <div className="meta">
                {jurisdictionName(permit.jurisdiction_id)}
                {permit.permit_type ? ` · ${permit.permit_type}` : ""}
              </div>
              {(permit.address || permit.city) && (
                <div className="meta">
                  {[permit.address, permit.city].filter(Boolean).join(", ")}
                </div>
              )}
              {permit.description && <p style={{ marginTop: "0.5rem" }}>{permit.description}</p>}
              {permit.structural_engineer_name ? (
                <p className="permit-engineer">
                  Structural engineer: <strong>{permit.structural_engineer_name}</strong>
                  {permit.structural_engineer_license
                    ? ` · PE ${permit.structural_engineer_license}`
                    : ""}
                  {permit.structural_engineer_firm ? ` · ${permit.structural_engineer_firm}` : ""}
                </p>
              ) : (
                permit.has_structural_plans && (
                  <p className="meta">Structural plans likely — engineer name not yet extracted.</p>
                )
              )}
              {permit.source_url && (
                <div className="comm-actions">
                  <a className="btn btn-ghost btn-sm" href={permit.source_url} target="_blank" rel="noreferrer">
                    View source
                  </a>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
