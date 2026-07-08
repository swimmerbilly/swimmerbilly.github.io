export type ProjectStatus = "active" | "on_hold" | "completed" | "archived";
export type CommunicationDirection = "inbound" | "outbound";

export interface Project {
  id: number;
  harvest_id: number | null;
  name: string;
  description: string | null;
  status: ProjectStatus;
  color: string;
  harvest_client_name: string | null;
  harvest_code: string | null;
  harvest_synced_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface HarvestStatus {
  configured: boolean;
  account_id: string | null;
  user_name: string | null;
}

export interface HarvestSyncResult {
  synced: number;
  created: number;
  updated: number;
  archived: number;
}

export interface GrasshopperStatus {
  configured: boolean;
  imap_configured: boolean;
  webhook_configured: boolean;
  imap_host: string | null;
  imap_user: string | null;
  imap_folder: string | null;
  webhook_url_hint: string | null;
  uses_work_outlook?: boolean;
}

export interface MailboxStatus {
  label: string;
  provider: string;
  configured: boolean;
  host: string | null;
  user: string | null;
  folder: string | null;
}

export interface MailboxAccountSyncResult {
  account: string;
  messages_scanned: number;
  created: number;
  skipped: number;
}

export interface MailboxSyncResult {
  accounts_synced: number;
  results: MailboxAccountSyncResult[];
  created: number;
  skipped: number;
}

export interface GrasshopperSyncResult {
  emails_scanned: number;
  events_found: number;
  voicemails_created: number;
  calls_created: number;
  texts_created: number;
  skipped: number;
}

export interface Email {
  id: number;
  project_id: number | null;
  direction: CommunicationDirection;
  from_address: string;
  to_address: string;
  subject: string;
  body: string;
  is_read: boolean;
  is_starred: boolean;
  account_label: string | null;
  external_message_id: string | null;
  received_at: string;
  created_at: string;
}

export interface TextMessage {
  id: number;
  project_id: number | null;
  direction: CommunicationDirection;
  contact_name: string | null;
  phone_number: string;
  body: string;
  is_read: boolean;
  grasshopper_message_id: string | null;
  sent_at: string;
  created_at: string;
}

export interface Call {
  id: number;
  project_id: number | null;
  direction: CommunicationDirection;
  contact_name: string | null;
  phone_number: string;
  duration_seconds: number | null;
  notes: string | null;
  grasshopper_message_id: string | null;
  called_at: string;
  created_at: string;
}

export interface Voicemail {
  id: number;
  project_id: number | null;
  contact_name: string | null;
  phone_number: string;
  transcript: string | null;
  audio_path: string | null;
  duration_seconds: number | null;
  is_listened: boolean;
  grasshopper_message_id: string | null;
  received_at: string;
  created_at: string;
}

export interface DashboardStats {
  project_count: number;
  active_projects: number;
  unread_emails: number;
  unread_texts: number;
  unlistened_voicemails: number;
  recent_calls: number;
  total_communications: number;
}

export interface AssistantStatus {
  configured: boolean;
  model: string;
  name: string;
}

export interface AssistantConversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface AssistantMessage {
  id: number;
  conversation_id: number;
  role: "user" | "assistant" | string;
  content: string;
  created_at: string;
}

export interface AssistantChatResponse {
  conversation: AssistantConversation;
  user_message: AssistantMessage;
  assistant_message: AssistantMessage;
}
