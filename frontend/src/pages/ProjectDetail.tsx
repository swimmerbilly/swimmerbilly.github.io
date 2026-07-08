import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { useCallNotepad } from "../components/NotepadProvider";
import { EmptyState, PageHeader, formatDate, useAsyncData } from "../components/ui";
import type { TimelineEntry } from "../types";

const TYPE_ICONS: Record<string, string> = {
  email: "✉",
  text: "💬",
  call: "📞",
  voicemail: "🔊",
};

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);
  const { openNotepad } = useCallNotepad();

  const { data: project, error: projectError, loading: projectLoading } = useAsyncData(() =>
    api.getProject(projectId)
  );
  const { data: timeline, loading: timelineLoading } = useAsyncData(() =>
    api.getProjectTimeline(projectId)
  );
  const { data: contacts, loading: contactsLoading } = useAsyncData(() =>
    api.getProjectContacts(projectId)
  );

  if (projectLoading) return <p className="meta">Loading project...</p>;
  if (projectError || !project) {
    return (
      <>
        <PageHeader title="Project" description="Not found" />
        <div className="error-banner">{projectError ?? "Project not found"}</div>
        <Link to="/projects" className="btn btn-ghost">
          Back to projects
        </Link>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title={project.name}
        description={project.harvest_client_name ?? project.description ?? "Project timeline and contacts"}
      />

      <div className="project-detail-header card">
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
          <span className="project-dot" style={{ background: project.color, marginTop: "0.4rem" }} />
          <div>
            <div className="meta" style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              <span className={`badge badge-${project.status}`}>{project.status.replace("_", " ")}</span>
              {project.harvest_code && <span className="badge badge-code">{project.harvest_code}</span>}
              {project.harvest_id !== null && <span className="badge badge-harvest">Harvest</span>}
            </div>
            {project.description && <p className="meta" style={{ marginTop: "0.5rem" }}>{project.description}</p>}
          </div>
        </div>
        <div className="project-detail-actions">
          <button className="btn btn-primary" onClick={() => openNotepad(project.id)}>
            Take call notes
          </button>
          <Link to="/projects" className="btn btn-ghost">
            All projects
          </Link>
        </div>
      </div>

      {contacts && contacts.length > 0 && (
        <div className="card project-contacts-card">
          <h3>People on this project</h3>
          <div className="contact-chips">
            {contacts.map((contact) => (
              <div key={`${contact.name}-${contact.phone}-${contact.email}`} className="contact-chip">
                <span className="contact-name">{contact.name}</span>
                {contact.roles.length > 0 && (
                  <span className="badge badge-role">{contact.roles.join(", ")}</span>
                )}
                <span className="meta">
                  {[contact.phone, contact.email].filter(Boolean).join(" · ")}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
      {contactsLoading && <p className="meta">Loading contacts...</p>}

      <h3 className="section-title">Timeline</h3>
      {timelineLoading && <p className="meta">Loading timeline...</p>}
      {!timelineLoading && timeline?.length === 0 && (
        <EmptyState message="No communications linked to this project yet." />
      )}
      <div className="timeline">
        {timeline?.map((entry: TimelineEntry) => (
          <div key={`${entry.type}-${entry.id}`} className={`timeline-item timeline-${entry.type}`}>
            <div className="timeline-icon">{TYPE_ICONS[entry.type] ?? "•"}</div>
            <div className="timeline-body">
              <div className="timeline-title">{entry.title}</div>
              <div className="meta">{formatDate(entry.occurred_at)}</div>
              <p>{entry.summary}</p>
              {entry.type === "call" &&
                Boolean(entry.meta.follow_up_at) &&
                !entry.meta.follow_up_completed && (
                <span className="badge badge-priority badge-priority-high">Follow-up due</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
