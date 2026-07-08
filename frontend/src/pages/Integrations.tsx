import { Link } from "react-router-dom";
import { useState } from "react";
import { api } from "../api/client";
import { PageHeader, useAsyncData } from "../components/ui";
import type { GrasshopperSyncResult, HarvestSyncResult, MailboxSyncResult } from "../types";

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
  const {
    data: mailboxes,
    loading: mailboxesLoading,
    reload: reloadMailboxes,
  } = useAsyncData(() => api.getMailboxStatus());

  const [harvestSyncing, setHarvestSyncing] = useState(false);
  const [grasshopperSyncing, setGrasshopperSyncing] = useState(false);
  const [emailSyncing, setEmailSyncing] = useState(false);
  const [harvestResult, setHarvestResult] = useState<HarvestSyncResult | null>(null);
  const [grasshopperResult, setGrasshopperResult] = useState<GrasshopperSyncResult | null>(null);
  const [emailResult, setEmailResult] = useState<MailboxSyncResult | null>(null);
  const [harvestError, setHarvestError] = useState<string | null>(null);
  const [grasshopperError, setGrasshopperError] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);

  const workMailbox = mailboxes?.find((m) => m.label === "work");
  const personalMailbox = mailboxes?.find((m) => m.label === "personal");
  const anyMailboxConfigured = mailboxes?.some((m) => m.configured);

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

  const syncEmails = async (account?: "work" | "personal") => {
    setEmailSyncing(true);
    setEmailError(null);
    setEmailResult(null);
    try {
      setEmailResult(await api.syncMailboxes(account));
      reloadMailboxes();
    } catch (err) {
      setEmailError(err instanceof Error ? err.message : "Email sync failed");
    } finally {
      setEmailSyncing(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Integrations"
        description="Connect Harvest, Outlook work email, Gmail personal email, and Grasshopper. Enter credentials on the Connect page."
      />

      <p className="meta" style={{ marginBottom: "1rem" }}>
        Need to add or update credentials? Go to <Link to="/setup">Connect your accounts</Link>.
      </p>

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
                Not connected. <Link to="/setup">Add Harvest credentials</Link>.
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
            <h3>Email · Outlook (work) + Gmail (personal)</h3>
            {mailboxesLoading ? (
              <p className="meta">Checking mailboxes...</p>
            ) : (
              <>
                {workMailbox?.configured ? (
                  <p className="meta">
                    Work Outlook: {workMailbox.user} @ {workMailbox.host}
                  </p>
                ) : (
                  <p className="meta">Work Outlook not configured — <Link to="/setup">connect work email</Link></p>
                )}
                {personalMailbox?.configured ? (
                  <p className="meta">
                    Personal Gmail: {personalMailbox.user} @ {personalMailbox.host}
                  </p>
                ) : (
                  <p className="meta">Personal Gmail not configured — <Link to="/setup">connect Gmail</Link> (optional)</p>
                )}
              </>
            )}
          </div>
          <button
            className="btn btn-primary"
            onClick={() => syncEmails()}
            disabled={!anyMailboxConfigured || emailSyncing}
          >
            {emailSyncing ? "Syncing..." : "Sync All Email"}
          </button>
        </div>

        <div className="setup-steps">
          <p className="meta"><strong>Outlook (company):</strong> Use an app password if MFA is on. Host is usually <code>outlook.office365.com</code>.</p>
          <p className="meta"><strong>Gmail (personal):</strong> Enable IMAP in Gmail settings and create a Google app password.</p>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "0.75rem" }}>
            <button className="btn btn-ghost" onClick={() => syncEmails("work")} disabled={!workMailbox?.configured || emailSyncing}>
              Sync Outlook only
            </button>
            <button className="btn btn-ghost" onClick={() => syncEmails("personal")} disabled={!personalMailbox?.configured || emailSyncing}>
              Sync Gmail only
            </button>
          </div>
        </div>

        {emailError && <div className="error-banner">{emailError}</div>}
        {emailResult && (
          <p className="sync-result">
            Synced {emailResult.accounts_synced} mailbox(es): {emailResult.created} new emails,{" "}
            {emailResult.skipped} skipped.
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
                {grasshopperStatus.uses_work_outlook ? " · using your Outlook work inbox" : ""}
              </p>
            ) : (
              <p className="meta">
                Connect <Link to="/setup">work Outlook</Link> and forward Grasshopper voicemails to that address.
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
            <li>In Grasshopper Settings → Notifications, add your <strong>company Outlook address</strong>.</li>
            <li>Enable voicemail-to-email (MP3 + transcription).</li>
            <li>Configure <code>WORK_EMAIL_IMAP_*</code> for Outlook — Grasshopper will use that inbox automatically.</li>
            <li>Click Sync from Inbox to import voicemails.</li>
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
