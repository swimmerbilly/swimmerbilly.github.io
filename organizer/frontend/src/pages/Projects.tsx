import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useCallNotepad } from "../components/NotepadProvider";
import {
  EmptyState,
  FormField,
  Modal,
  PageHeader,
  SubmitForm,
  useAsyncData,
} from "../components/ui";
import type { HarvestSyncResult, Project, ProjectStatus } from "../types";

const STATUS_OPTIONS: ProjectStatus[] = ["active", "on_hold", "completed", "archived"];

export default function ProjectsPage() {
  const { openNotepad } = useCallNotepad();
  const { data: projects, error, loading, reload } = useAsyncData(() => api.getProjects());
  const {
    data: harvestStatus,
    error: harvestError,
    loading: harvestLoading,
    reload: reloadHarvest,
  } = useAsyncData(() => api.getHarvestStatus());
  const [showModal, setShowModal] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<HarvestSyncResult | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<ProjectStatus>("active");
  const [color, setColor] = useState("#3b82f6");

  const harvestProjects = projects?.filter((p) => p.harvest_id !== null) ?? [];
  const localProjects = projects?.filter((p) => p.harvest_id === null) ?? [];

  const handleSync = async () => {
    setSyncing(true);
    setSyncError(null);
    setSyncResult(null);
    try {
      const result = await api.syncHarvestProjects();
      setSyncResult(result);
      reload();
      reloadHarvest();
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Harvest sync failed");
    } finally {
      setSyncing(false);
    }
  };

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    await api.createProject({ name, description: description || null, status, color });
    setShowModal(false);
    setName("");
    setDescription("");
    setStatus("active");
    setColor("#3b82f6");
    reload();
  };

  const handleDelete = async (project: Project) => {
    if (project.harvest_id !== null) return;
    if (!confirm(`Delete project "${project.name}"?`)) return;
    try {
      await api.deleteProject(project.id);
      reload();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Could not delete project");
    }
  };

  const renderProject = (project: Project) => (
    <div key={project.id} className="list-item">
      <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
        <span className="project-dot" style={{ background: project.color, marginTop: "0.4rem" }} />
        <div>
          <div className="title">
            {project.name}
            {project.harvest_id !== null && <span className="badge badge-harvest">Harvest</span>}
          </div>
          {project.harvest_client_name && (
            <p className="meta">{project.harvest_client_name}</p>
          )}
          {project.description && <p className="meta">{project.description}</p>}
          <div className="meta" style={{ marginTop: "0.5rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <span className={`badge badge-${project.status}`}>
              {project.status.replace("_", " ")}
            </span>
            {project.harvest_code && <span className="badge badge-code">{project.harvest_code}</span>}
          </div>
          <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <button className="btn btn-ghost" onClick={() => openNotepad(project.id)}>
              Take call notes
            </button>
            <Link className="btn btn-ghost" to={`/calls?project=${project.id}`}>
              View call notes
            </Link>
          </div>
        </div>
      </div>
      {project.harvest_id === null ? (
        <button className="btn btn-ghost" onClick={() => handleDelete(project)}>
          Delete
        </button>
      ) : (
        <span className="meta">Synced from Harvest</span>
      )}
    </div>
  );

  return (
    <>
      <PageHeader
        title="Projects"
        description="Projects sync from Harvest. Link emails, texts, calls, and voicemails to them."
      />

      <div className="card harvest-card">
        <div className="harvest-card-header">
          <div>
            <h3>Harvest Connection</h3>
            {harvestLoading ? (
              <p className="meta">Checking connection...</p>
            ) : harvestStatus?.configured ? (
              <p className="meta">
                Connected as {harvestStatus.user_name || "Harvest user"}
                {harvestStatus.account_id ? ` · Account ${harvestStatus.account_id}` : ""}
              </p>
            ) : (
              <p className="meta">
                Not configured. Add your Harvest credentials to{" "}
                <code>organizer/backend/.env</code> (see <code>.env.example</code>).
              </p>
            )}
          </div>
          <button
            className="btn btn-primary"
            onClick={handleSync}
            disabled={!harvestStatus?.configured || syncing}
          >
            {syncing ? "Syncing..." : "Sync from Harvest"}
          </button>
        </div>
        {harvestError && <div className="error-banner">{harvestError}</div>}
        {syncError && <div className="error-banner">{syncError}</div>}
        {syncResult && (
          <p className="sync-result">
            Synced {syncResult.synced} projects ({syncResult.created} new, {syncResult.updated}{" "}
            updated, {syncResult.archived} archived locally).
          </p>
        )}
      </div>

      <div className="toolbar">
        <span>{projects?.length ?? 0} projects</span>
        <button className="btn btn-ghost" onClick={() => setShowModal(true)}>
          + Local Project
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {loading && <p>Loading projects...</p>}

      {!loading && projects?.length === 0 && (
        <EmptyState
          message={
            harvestStatus?.configured
              ? "No projects yet. Click Sync from Harvest to pull your projects."
              : "Configure Harvest, then sync your projects."
          }
          action={
            harvestStatus?.configured ? (
              <button className="btn btn-primary" onClick={handleSync} disabled={syncing}>
                Sync from Harvest
              </button>
            ) : undefined
          }
        />
      )}

      {harvestProjects.length > 0 && (
        <>
          <h3 className="section-title">From Harvest ({harvestProjects.length})</h3>
          <div className="list">{harvestProjects.map(renderProject)}</div>
        </>
      )}

      {localProjects.length > 0 && (
        <>
          <h3 className="section-title">Local Only ({localProjects.length})</h3>
          <div className="list">{localProjects.map(renderProject)}</div>
        </>
      )}

      <Modal title="New Local Project" isOpen={showModal} onClose={() => setShowModal(false)}>
        <SubmitForm onSubmit={handleCreate} onCancel={() => setShowModal(false)} submitLabel="Create">
          <p className="meta" style={{ marginBottom: "1rem" }}>
            Local projects are not synced to Harvest. Use this for personal items only.
          </p>
          <FormField label="Name">
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </FormField>
          <FormField label="Description">
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </FormField>
          <FormField label="Status">
            <select value={status} onChange={(e) => setStatus(e.target.value as ProjectStatus)}>
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s.replace("_", " ")}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Color">
            <input type="color" value={color} onChange={(e) => setColor(e.target.value)} />
          </FormField>
        </SubmitForm>
      </Modal>
    </>
  );
}
