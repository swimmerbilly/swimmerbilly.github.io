import { useEffect, useRef, useState, type FormEvent } from "react";
import { api } from "../api/client";
import type { CallerRole, Project } from "../types";

const CALLER_ROLES: { value: CallerRole; label: string }[] = [
  { value: "architect", label: "Architect" },
  { value: "contractor", label: "Contractor" },
  { value: "client", label: "Client" },
  { value: "vendor", label: "Vendor" },
  { value: "other", label: "Other" },
];

interface CallNotepadProps {
  open: boolean;
  onClose: () => void;
  initialProjectId?: number | null;
}

export default function CallNotepad({ open, onClose, initialProjectId = null }: CallNotepadProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState<string>("");
  const [contactName, setContactName] = useState("");
  const [callerRole, setCallerRole] = useState<CallerRole>("contractor");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const notesRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!open) return;
    api.getProjects().then(setProjects).catch(() => setProjects([]));
    if (initialProjectId) {
      setProjectId(String(initialProjectId));
    }
    setTimeout(() => notesRef.current?.focus(), 100);
  }, [open, initialProjectId]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  const resetForm = (keepProject = true) => {
    setContactName("");
    setCallerRole("contractor");
    setPhoneNumber("");
    setNotes("");
    setError(null);
    setSaved(false);
    if (!keepProject) setProjectId("");
  };

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    if (!projectId) {
      setError("Pick a project so this note gets filed correctly.");
      return;
    }
    if (!contactName.trim()) {
      setError("Who's on the call?");
      return;
    }
    if (!notes.trim()) {
      setError("Add your call notes before saving.");
      return;
    }

    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      await api.createQuickCallNote({
        project_id: parseInt(projectId, 10),
        contact_name: contactName.trim(),
        caller_role: callerRole,
        notes: notes.trim(),
        phone_number: phoneNumber.trim() || null,
      });
      setSaved(true);
      resetForm(true);
      notesRef.current?.focus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save call note");
    } finally {
      setSaving(false);
    }
  };

  if (!open) return null;

  const activeProjects = projects.filter((p) => p.status === "active");

  return (
    <div className="notepad-overlay" onClick={onClose}>
      <aside className="notepad-panel" onClick={(e) => e.stopPropagation()}>
        <header className="notepad-header">
          <div>
            <h3>Call Notepad</h3>
            <p className="meta">Jot notes during the call — saved to the right project.</p>
          </div>
          <button className="btn btn-ghost" onClick={onClose} aria-label="Close notepad">
            ✕
          </button>
        </header>

        <form className="notepad-form" onSubmit={handleSave}>
          <label className="notepad-field">
            <span>Project</span>
            <select value={projectId} onChange={(e) => setProjectId(e.target.value)} required>
              <option value="">Select project…</option>
              {activeProjects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                  {project.harvest_client_name ? ` · ${project.harvest_client_name}` : ""}
                </option>
              ))}
            </select>
          </label>

          <div className="notepad-row">
            <label className="notepad-field">
              <span>Who's calling?</span>
              <input
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
                placeholder="e.g. Mike at ABC Architecture"
                required
              />
            </label>
            <label className="notepad-field">
              <span>Role</span>
              <select
                value={callerRole}
                onChange={(e) => setCallerRole(e.target.value as CallerRole)}
              >
                {CALLER_ROLES.map((role) => (
                  <option key={role.value} value={role.value}>
                    {role.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="notepad-field">
            <span>Phone (optional)</span>
            <input
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              placeholder="(555) 123-4567"
            />
          </label>

          <label className="notepad-field notepad-notes-field">
            <span>Notes</span>
            <textarea
              ref={notesRef}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="What do they need? Materials, dimensions, schedule, RFIs..."
              rows={10}
              required
            />
          </label>

          {error && <div className="error-banner">{error}</div>}
          {saved && <p className="sync-result">Saved to project. Ready for the next note.</p>}

          <div className="notepad-actions">
            <button type="button" className="btn btn-ghost" onClick={() => resetForm(true)}>
              Clear
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Saving..." : "Save to project"}
            </button>
          </div>
        </form>
      </aside>
    </div>
  );
}
