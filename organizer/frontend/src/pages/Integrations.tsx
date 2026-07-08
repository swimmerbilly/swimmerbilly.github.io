import { useState } from "react";
import { api } from "../api/client";
import { PageHeader, useAsyncData } from "../components/ui";
import type { GrasshopperSyncResult, HarvestSyncResult } from "../types";

export default function IntegrationsPage() {
  const {
    data: harvestStatus,
    loading: harvestLoading,
    reload: reloadHarvest,
  } = useAsyncData(() => api.getHarvestStatus());
  const {
    data: grasshopperStatus,
    loading: grasshopperLoading,
    reload: reloadGrasshopper,
  } = useAsyncData(() => api.getGrasshopperStatus());

  const [harvestSyncing, setHarvestSyncing] = useState(false);
  const [grasshopperSyncing, setGrasshopperSyncing] = useState(false);
  const [harvestResult, setHarvestResult] = useState<HarvestSyncResult | null>(null);
  const [grasshopperResult, setGrasshopperResult] = useState<GrasshopperSyncResult | null>(null);
  const [harvestError, setHarvestError] = useState<string | null>(null);
  const [grasshopperError, setGrasshopperError] = useState<string | null>(null);

  const syncHarvest = async () => {
    setHarvestSyncing(true);
    setHarvestError(null);
    setHarvestResult(null);
    try {
      setHarvestResult(await api.syncHarvestProjects());
      reloadHarvest();
    } catch (err) {
      setHarvestError(err instanceof Error ? err.message : "Harvest sync failed");
    } finally {
      setHarvestSyncing(false);
    }
  };

  const syncGrasshopper = async () => {
    setGrasshopperSyncing(true);
    setGrasshopperError(null);
    setGrasshopperResult(null);
    try {
      setGrasshopperResult(await api.syncGrasshopper());
      reloadGrasshopper();
    } catch (err) {
      setGrasshopperError(err instanceof Error ? err.message : "Grasshopper sync failed");
    } finally {
      setGrasshopperSyncing(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Integrations"
        description="Connect Harvest for projects and Grasshopper for phone communications."
      />

      <div className="card harvest-card">
        <div className="harvest-card-header">
          <div>
            <h3>Harvest · Projects</h3>
            {harvestLoading ? (
              <p className="meta">Checking connection...</p>
            ) : harvestStatus?.configured ? (
              <p className="meta">
                Connected as {harvestStatus.user_name || "Harvest user"}
                {harvestStatus.account_id ? ` · Account ${harvestStatus.account_id}` : ""}
              </p>
            ) : (
              <p className="meta">
                Add <code>HARVEST_ACCESS_TOKEN</code> and <code>HARVEST_ACCOUNT_ID</code> to{" "}
                <code>organizer/backend/.env</code>.
              </p>
            )}
          </div>
          <button
            className="btn btn-primary"
            onClick={syncHarvest}
            disabled={!harvestStatus?.configured || harvestSyncing}
          >
            {harvestSyncing ? "Syncing..." : "Sync Projects"}
          </button>
        </div>
        {harvestError && <div className="error-banner">{harvestError}</div>}
        {harvestResult && (
          <p className="sync-result">
            Synced {harvestResult.synced} projects ({harvestResult.created} new,{" "}
            {harvestResult.updated} updated, {harvestResult.archived} archived).
          </p>
        )}
      </div>

      <div className="card harvest-card">
        <div className="harvest-card-header">
          <div>
            <h3>Grasshopper · Phone</h3>
            {grasshopperLoading ? (
              <p className="meta">Checking connection...</p>
            ) : grasshopperStatus?.imap_configured ? (
              <p className="meta">
                IMAP inbox: {grasshopperStatus.imap_user} @ {grasshopperStatus.imap_host}
                {grasshopperStatus.imap_folder ? ` · ${grasshopperStatus.imap_folder}` : ""}
              </p>
            ) : (
              <p className="meta">
                Grasshopper has no public API. Configure IMAP credentials in{" "}
                <code>organizer/backend/.env</code> and forward Grasshopper voicemail emails to
                that inbox.
              </p>
            )}
            {grasshopperStatus?.webhook_configured && (
              <p className="meta" style={{ marginTop: "0.5rem" }}>
                Webhook ready at <code>POST /api/grasshopper/webhook</code> for texts/calls via
                Zapier or custom automations.
              </p>
            )}
          </div>
          <button
            className="btn btn-primary"
            onClick={syncGrasshopper}
            disabled={!grasshopperStatus?.imap_configured || grasshopperSyncing}
          >
            {grasshopperSyncing ? "Syncing..." : "Sync from Inbox"}
          </button>
        </div>

        <div className="setup-steps">
          <p className="meta"><strong>Setup steps:</strong></p>
          <ol className="meta">
            <li>In Grasshopper, go to Settings → Notifications and add your IMAP email address.</li>
            <li>Enable voicemail-to-email (MP3 + transcription).</li>
            <li>Add IMAP credentials to <code>organizer/backend/.env</code>.</li>
            <li>Click Sync from Inbox to import voicemails (and any emailed call/text alerts).</li>
          </ol>
        </div>

        {grasshopperError && <div className="error-banner">{grasshopperError}</div>}
        {grasshopperResult && (
          <p className="sync-result">
            Scanned {grasshopperResult.emails_scanned} Grasshopper emails, found{" "}
            {grasshopperResult.events_found} events ({grasshopperResult.voicemails_created}{" "}
            voicemails, {grasshopperResult.calls_created} calls, {grasshopperResult.texts_created}{" "}
            texts, {grasshopperResult.skipped} skipped).
          </p>
        )}
      </div>
    </>
  );
}
