import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Project, ProjectSuggestion } from "../types";

type CommType = "email" | "text" | "voicemail" | "call";

interface ProjectLinkBarProps {
  commType: CommType;
  commId: number;
  projectId: number | null;
  projectName?: string | null;
  projectColor?: string | null;
  projects: Project[];
  onUpdated: () => void;
}

export default function ProjectLinkBar({
  commType,
  commId,
  projectId,
  projectName,
  projectColor,
  projects,
  onUpdated,
}: ProjectLinkBarProps) {
  const [suggestions, setSuggestions] = useState<ProjectSuggestion[]>([]);
  const [editing, setEditing] = useState(false);
  const [pickId, setPickId] = useState("");
  const [busy, setBusy] = useState(false);

  const isLinked = projectId !== null && !editing;

  useEffect(() => {
    if (projectId && !editing) {
      setSuggestions([]);
      return;
    }
    api.getLinkSuggestion(commType, commId).then(setSuggestions).catch(() => setSuggestions([]));
  }, [commType, commId, projectId, editing]);

  const applyProject = async (targetId: number | null) => {
    setBusy(true);
    try {
      if (targetId === null) {
        if (commType === "email") await api.updateEmail(commId, { project_id: null });
        else if (commType === "text") await api.updateText(commId, { project_id: null });
        else if (commType === "voicemail") await api.updateVoicemail(commId, { project_id: null });
        else await api.updateCall(commId, { project_id: null });
      } else {
        await api.linkCommToProject(commType, commId, targetId);
      }
      setEditing(false);
      setPickId("");
      onUpdated();
    } finally {
      setBusy(false);
    }
  };

  const topSuggestion = suggestions[0];

  if (isLinked && projectName) {
    return (
      <div className="project-filing linked" onClick={(e) => e.stopPropagation()}>
        <span className="badge badge-project-linked">
          <span
            className="project-dot"
            style={{ background: projectColor ?? "#3b82f6" }}
          />
          <Link to={`/projects/${projectId}`}>{projectName}</Link>
        </span>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={() => setEditing(true)}
          disabled={busy}
        >
          Change
        </button>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={() => applyProject(null)}
          disabled={busy}
        >
          Unlink
        </button>
      </div>
    );
  }

  return (
    <div className="project-filing" onClick={(e) => e.stopPropagation()}>
      {topSuggestion && (
        <button
          type="button"
          className="btn btn-ghost btn-sm link-suggest-btn"
          onClick={() => applyProject(topSuggestion.project_id)}
          disabled={busy}
        >
          Suggested: {topSuggestion.project_name}
        </button>
      )}
      <select
        value={pickId}
        onChange={(e) => setPickId(e.target.value)}
        aria-label="Pick project"
      >
        <option value="">Pick project…</option>
        {projects.map((project) => (
          <option key={project.id} value={project.id}>
            {project.name}
            {project.harvest_client_name ? ` · ${project.harvest_client_name}` : ""}
          </option>
        ))}
      </select>
      <button
        type="button"
        className="btn btn-primary btn-sm"
        onClick={() => pickId && applyProject(parseInt(pickId, 10))}
        disabled={busy || !pickId}
      >
        {busy ? "Saving…" : "Link"}
      </button>
      {editing && projectId && (
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={() => setEditing(false)}
          disabled={busy}
        >
          Cancel
        </button>
      )}
    </div>
  );
}
