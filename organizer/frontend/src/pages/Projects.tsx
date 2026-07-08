import { useState, type FormEvent } from "react";
import { api } from "../api/client";
import {
  EmptyState,
  FormField,
  Modal,
  PageHeader,
  SubmitForm,
  useAsyncData,
} from "../components/ui";
import type { Project, ProjectStatus } from "../types";

const STATUS_OPTIONS: ProjectStatus[] = ["active", "on_hold", "completed", "archived"];

export default function ProjectsPage() {
  const { data: projects, error, loading, reload } = useAsyncData(() => api.getProjects());
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<ProjectStatus>("active");
  const [color, setColor] = useState("#3b82f6");

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
    if (!confirm(`Delete project "${project.name}"?`)) return;
    await api.deleteProject(project.id);
    reload();
  };

  return (
    <>
      <PageHeader
        title="Projects"
        description="Organize your work and link communications to each project."
      />

      <div className="toolbar">
        <span>{projects?.length ?? 0} projects</span>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          + New Project
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {loading && <p>Loading projects...</p>}

      {!loading && projects?.length === 0 && (
        <EmptyState
          message="No projects yet."
          action={
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>
              Create your first project
            </button>
          }
        />
      )}

      <div className="list">
        {projects?.map((project) => (
          <div key={project.id} className="list-item">
            <div style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
              <span className="project-dot" style={{ background: project.color, marginTop: "0.4rem" }} />
              <div>
                <div className="title">{project.name}</div>
                {project.description && (
                  <p className="meta">{project.description}</p>
                )}
                <div className="meta" style={{ marginTop: "0.5rem" }}>
                  <span className={`badge badge-${project.status}`}>{project.status.replace("_", " ")}</span>
                </div>
              </div>
            </div>
            <button className="btn btn-ghost" onClick={() => handleDelete(project)}>
              Delete
            </button>
          </div>
        ))}
      </div>

      <Modal title="New Project" isOpen={showModal} onClose={() => setShowModal(false)}>
        <SubmitForm onSubmit={handleCreate} onCancel={() => setShowModal(false)} submitLabel="Create">
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
