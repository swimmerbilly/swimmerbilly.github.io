export type ProjectStatus = "active" | "on_hold" | "completed" | "archived";
export type CommunicationDirection = "inbound" | "outbound";
export type CallerRole = "architect" | "contractor" | "client" | "vendor" | "other";

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
  project_name: string | null;
  direction: CommunicationDirection;
  contact_name: string | null;
  caller_role: CallerRole | null;
  phone_number: string;
  duration_seconds: number | null;
  notes: string | null;
  grasshopper_message_id: string | null;
  follow_up_at: string | null;
  follow_up_completed: boolean;
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

export interface ChecklistItem {
  id: number;
  text: string;
  priority: string;
  is_completed: boolean;
  is_user_added: boolean;
  sort_order: number;
  created_at: string;
}

export interface DayPlan {
  id: number;
  plan_date: string;
  greeting: string;
  today_focus: string[];
  week_focus: string[];
  month_focus: string[];
  generated_at: string;
  checklist_items: ChecklistItem[];
  wrap_up_summary: string | null;
  wrap_up_tomorrow: string[];
  wrap_up_completed: string[];
  wrap_up_slipped: string[];
  wrap_up_generated_at: string | null;
  weekly_review_stalled: string[];
  weekly_review_gaps: string[];
  weekly_review_priorities: string[];
  weekly_review_generated_at: string | null;
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

export interface AssistantAction {
  type: string;
  label: string;
  params: Record<string, number | string | boolean>;
}

export interface AssistantChatResponse {
  conversation: AssistantConversation;
  user_message: AssistantMessage;
  assistant_message: AssistantMessage;
  actions: AssistantAction[];
}

export interface AttentionItem {
  priority: number;
  type: string;
  id: number;
  title: string;
  detail: string;
  href: string;
  occurred_at: string;
}

export interface TimelineEntry {
  type: string;
  id: number;
  occurred_at: string;
  title: string;
  summary: string;
  body_preview: string | null;
  meta: Record<string, unknown>;
}

export interface ProjectContact {
  name: string;
  phone: string | null;
  email: string | null;
  roles: string[];
  sources: string[];
  touch_count: number;
}

export interface ProjectSuggestion {
  project_id: number;
  project_name: string;
  confidence: number;
}
