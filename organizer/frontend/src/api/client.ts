import type {
  Call,
  DashboardStats,
  Email,
  GrasshopperStatus,
  GrasshopperSyncResult,
  HarvestStatus,
  HarvestSyncResult,
  Project,
  TextMessage,
  Voicemail,
} from "../types";

const API_BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  getStats: () => request<DashboardStats>("/dashboard/stats"),

  getProjects: () => request<Project[]>("/projects"),
  createProject: (data: Pick<Project, "name" | "description" | "status" | "color">) =>
    request<Project>("/projects", { method: "POST", body: JSON.stringify(data) }),
  deleteProject: (id: number) =>
    request<void>(`/projects/${id}`, { method: "DELETE" }),

  getHarvestStatus: () => request<HarvestStatus>("/harvest/status"),
  syncHarvestProjects: () =>
    request<HarvestSyncResult>("/harvest/sync", { method: "POST" }),

  getGrasshopperStatus: () => request<GrasshopperStatus>("/grasshopper/status"),
  syncGrasshopper: (sinceDays = 30) =>
    request<GrasshopperSyncResult>(`/grasshopper/sync?since_days=${sinceDays}`, {
      method: "POST",
    }),

  getEmails: () => request<Email[]>("/emails"),
  createEmail: (data: Omit<Email, "id" | "created_at" | "received_at">) =>
    request<Email>("/emails", { method: "POST", body: JSON.stringify(data) }),
  updateEmail: (id: number, data: Partial<Pick<Email, "is_read" | "is_starred" | "project_id">>) =>
    request<Email>(`/emails/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  getTexts: () => request<TextMessage[]>("/texts"),
  createText: (data: Omit<TextMessage, "id" | "created_at" | "sent_at" | "grasshopper_message_id">) =>
    request<TextMessage>("/texts", { method: "POST", body: JSON.stringify(data) }),
  updateText: (id: number, data: Partial<Pick<TextMessage, "is_read" | "project_id">>) =>
    request<TextMessage>(`/texts/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  getCalls: () => request<Call[]>("/calls"),
  createCall: (data: Omit<Call, "id" | "created_at" | "called_at" | "grasshopper_message_id">) =>
    request<Call>("/calls", { method: "POST", body: JSON.stringify(data) }),

  getVoicemails: () => request<Voicemail[]>("/voicemails"),
  createVoicemail: (data: Omit<Voicemail, "id" | "created_at" | "received_at" | "grasshopper_message_id">) =>
    request<Voicemail>("/voicemails", { method: "POST", body: JSON.stringify(data) }),
  updateVoicemail: (
    id: number,
    data: Partial<Pick<Voicemail, "is_listened" | "project_id" | "transcript">>
  ) =>
    request<Voicemail>(`/voicemails/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
};
