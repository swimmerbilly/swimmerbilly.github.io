import type {
  AssistantChatResponse,
  AssistantConversation,
  AssistantMessage,
  AssistantStatus,
  Call,
  CallerRole,
  DashboardStats,
  Email,
  GrasshopperStatus,
  GrasshopperSyncResult,
  HarvestStatus,
  HarvestSyncResult,
  MailboxStatus,
  MailboxSyncResult,
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
    try {
      const parsed = JSON.parse(message) as { detail?: string | { msg?: string }[] };
      if (typeof parsed.detail === "string") {
        throw new Error(parsed.detail);
      }
    } catch (parseError) {
      if (parseError instanceof Error && !message.startsWith("{")) {
        throw parseError;
      }
    }
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

  getMailboxStatus: () => request<MailboxStatus[]>("/mailboxes/status"),
  syncMailboxes: (account?: "work" | "personal") => {
    const query = account ? `?account=${account}` : "";
    return request<MailboxSyncResult>(`/mailboxes/sync${query}`, { method: "POST" });
  },

  getAssistantStatus: () => request<AssistantStatus>("/assistant/status"),
  getAssistantConversations: () => request<AssistantConversation[]>("/assistant/conversations"),
  createAssistantConversation: () =>
    request<AssistantConversation>("/assistant/conversations", { method: "POST" }),
  getAssistantMessages: (conversationId: number) =>
    request<AssistantMessage[]>(`/assistant/conversations/${conversationId}/messages`),
  deleteAssistantConversation: (conversationId: number) =>
    request<void>(`/assistant/conversations/${conversationId}`, { method: "DELETE" }),
  chatWithAssistant: (message: string, conversationId?: number) =>
    request<AssistantChatResponse>("/assistant/chat", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id: conversationId ?? null }),
    }),
  getAssistantBriefing: (conversationId?: number) => {
    const query = conversationId ? `?conversation_id=${conversationId}` : "";
    return request<AssistantChatResponse>(`/assistant/briefing${query}`, { method: "POST" });
  },

  getEmails: () => request<Email[]>("/emails"),
  createEmail: (data: Omit<Email, "id" | "created_at" | "received_at" | "account_label" | "external_message_id">) =>
    request<Email>("/emails", { method: "POST", body: JSON.stringify(data) }),
  updateEmail: (id: number, data: Partial<Pick<Email, "is_read" | "is_starred" | "project_id">>) =>
    request<Email>(`/emails/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  getTexts: () => request<TextMessage[]>("/texts"),
  createText: (data: Omit<TextMessage, "id" | "created_at" | "sent_at" | "grasshopper_message_id">) =>
    request<TextMessage>("/texts", { method: "POST", body: JSON.stringify(data) }),
  updateText: (id: number, data: Partial<Pick<TextMessage, "is_read" | "project_id">>) =>
    request<TextMessage>(`/texts/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  getCalls: (projectId?: number) =>
    request<Call[]>(projectId ? `/calls?project_id=${projectId}` : "/calls"),
  createQuickCallNote: (data: {
    project_id: number;
    contact_name: string;
    caller_role?: CallerRole | null;
    notes: string;
    phone_number?: string | null;
  }) => request<Call>("/calls/quick-note", { method: "POST", body: JSON.stringify(data) }),
  createCall: (data: Omit<Call, "id" | "created_at" | "called_at" | "grasshopper_message_id" | "project_name">) =>
    request<Call>("/calls", { method: "POST", body: JSON.stringify(data) }),
  updateCall: (
    id: number,
    data: Partial<Pick<Call, "project_id" | "notes" | "caller_role">>
  ) => request<Call>(`/calls/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  getProjectCalls: (projectId: number) => request<Call[]>(`/projects/${projectId}/calls`),

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
