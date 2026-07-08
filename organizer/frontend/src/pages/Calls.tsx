import { useMemo, useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import {
  EmptyState,
  FormField,
  Modal,
  PageHeader,
  SubmitForm,
  formatDate,
  formatDuration,
  useAsyncData,
} from "../components/ui";
import type { CallerRole, CommunicationDirection, Project } from "../types";

const ROLE_LABELS: Record<CallerRole, string> = {
  architect: "Architect",
  contractor: "Contractor",
  client: "Client",
  vendor: "Vendor",
  other: "Other",
};

export default function CallsPage() {
  const [searchParams] = useSearchParams();
  const projectFilter = searchParams.get("project");
  const projectFilterId = projectFilter ? parseInt(projectFilter, 10) : undefined;

  const { data: calls, error, loading, reload } = useAsyncData(
    () => api.getCalls(projectFilterId),
    [projectFilterId]
  );
  const { data: projects } = useAsyncData(() => api.getProjects());

  const [showModal, setShowModal] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState("");
  const [contactName, setContactName] = useState("");
  const [durationSeconds, setDurationSeconds] = useState("");
  const [notes, setNotes] = useState("");
  const [direction, setDirection] = useState<CommunicationDirection>("inbound");
  const [projectId, setProjectId] = useState("");
  const [callerRole, setCallerRole] = useState<CallerRole>("contractor");

  const filteredProject = useMemo(
    () => projects?.find((p) => p.id === projectFilterId),
    [projects, projectFilterId]
  );

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    await api.createCall({
      project_id: projectId ? parseInt(projectId, 10) : null,
      direction,
      contact_name: contactName || null,
      caller_role: callerRole,
      phone_number: phoneNumber,
      duration_seconds: durationSeconds ? parseInt(durationSeconds, 10) : null,
      notes: notes || null,
    });
    setShowModal(false);
    setPhoneNumber("");
    setContactName("");
    setDurationSeconds("");
    setNotes("");
    setProjectId("");
    reload();
  };

  return (
    <>
      <PageHeader
        title="Call Notes"
        description="Notes from architects, contractors, and clients — organized by project. Use the Call Notes button (bottom-right) during a call."
      />

      {filteredProject && (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <p>
            Showing notes for <strong>{filteredProject.name}</strong>.{" "}
            <Link to="/calls">Show all calls</Link>
          </p>
        </div>
      )}

      <div className="toolbar">
        <span>{calls?.length ?? 0} call notes</span>
        <button className="btn btn-ghost" onClick={() => setShowModal(true)}>
          + Full log entry
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {loading && <p>Loading call notes...</p>}

      {!loading && calls?.length === 0 && (
        <EmptyState message="No call notes yet. Click Call Notes (bottom-right) when someone rings." />
      )}

      <div className="list">
        {calls?.map((call) => (
          <div key={call.id} className="list-item">
            <div>
              <div className="title">
                {call.contact_name || call.phone_number}
                {call.caller_role && (
                  <span className={`badge badge-role badge-${call.caller_role}`}>
                    {ROLE_LABELS[call.caller_role]}
                  </span>
                )}
              </div>
              {call.project_name && (
                <p className="meta">
                  <Link to={`/calls?project=${call.project_id}`}>{call.project_name}</Link>
                </p>
              )}
              <div className="meta">
                {formatDate(call.called_at)}
                {call.duration_seconds ? ` · ${formatDuration(call.duration_seconds)}` : ""}
              </div>
              {call.notes && <p style={{ marginTop: "0.75rem", whiteSpace: "pre-wrap" }}>{call.notes}</p>}
            </div>
          </div>
        ))}
      </div>

      <Modal title="Log Call" isOpen={showModal} onClose={() => setShowModal(false)}>
        <SubmitForm onSubmit={handleCreate} onCancel={() => setShowModal(false)}>
          <FormField label="Project">
            <select value={projectId} onChange={(e) => setProjectId(e.target.value)}>
              <option value="">No project</option>
              {projects?.map((project: Project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Direction">
            <select
              value={direction}
              onChange={(e) => setDirection(e.target.value as CommunicationDirection)}
            >
              <option value="inbound">Inbound</option>
              <option value="outbound">Outbound</option>
            </select>
          </FormField>
          <FormField label="Contact Name">
            <input value={contactName} onChange={(e) => setContactName(e.target.value)} />
          </FormField>
          <FormField label="Role">
            <select value={callerRole} onChange={(e) => setCallerRole(e.target.value as CallerRole)}>
              {Object.entries(ROLE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Phone Number">
            <input value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} required />
          </FormField>
          <FormField label="Duration (seconds)">
            <input
              type="number"
              value={durationSeconds}
              onChange={(e) => setDurationSeconds(e.target.value)}
              min="0"
            />
          </FormField>
          <FormField label="Notes">
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={4} />
          </FormField>
        </SubmitForm>
      </Modal>
    </>
  );
}
