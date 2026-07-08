import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ProjectSuggestion } from "../types";

interface ProjectLinkSuggestProps {
  commType: "email" | "text" | "voicemail" | "call";
  commId: number;
  projectId: number | null;
  onLinked: () => void;
}

export default function ProjectLinkSuggest({
  commType,
  commId,
  projectId,
  onLinked,
}: ProjectLinkSuggestProps) {
  const [suggestions, setSuggestions] = useState<ProjectSuggestion[]>([]);
  const [linking, setLinking] = useState(false);

  useEffect(() => {
    if (projectId) {
      setSuggestions([]);
      return;
    }
    api.getLinkSuggestion(commType, commId).then(setSuggestions).catch(() => setSuggestions([]));
  }, [commType, commId, projectId]);

  if (projectId || suggestions.length === 0) return null;

  const top = suggestions[0];

  const handleLink = async () => {
    setLinking(true);
    try {
      await api.linkCommToProject(commType, commId, top.project_id);
      onLinked();
    } finally {
      setLinking(false);
    }
  };

  return (
    <div className="link-suggest" onClick={(e) => e.stopPropagation()}>
      <span className="meta">Suggested: {top.project_name}</span>
      <button className="btn btn-ghost btn-sm" onClick={handleLink} disabled={linking}>
        {linking ? "Linking..." : "Link to project"}
      </button>
    </div>
  );
}
