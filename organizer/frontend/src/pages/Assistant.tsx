import { useEffect, useRef, useState, type FormEvent } from "react";
import { api } from "../api/client";
import { PageHeader, useAsyncData } from "../components/ui";
import type { AssistantConversation, AssistantMessage } from "../types";

const QUICK_ACTIONS = [
  "What needs my attention right now?",
  "Summarize my unread emails, texts, and voicemails.",
  "Draft a professional follow-up email for my most recent unread message.",
  "Which Harvest project should I focus on today?",
];

export default function AssistantPage() {
  const { data: status, loading: statusLoading } = useAsyncData(() => api.getAssistantStatus());
  const {
    data: conversations,
    loading: conversationsLoading,
    reload: reloadConversations,
  } = useAsyncData(() => api.getAssistantConversations());

  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<AssistantMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeConversation = conversations?.find((c) => c.id === activeConversationId) ?? null;

  useEffect(() => {
    if (!activeConversationId) {
      setMessages([]);
      return;
    }
    api.getAssistantMessages(activeConversationId).then(setMessages).catch(() => setMessages([]));
  }, [activeConversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const handleNewConversation = async () => {
    const conversation = await api.createAssistantConversation();
    reloadConversations();
    setActiveConversationId(conversation.id);
    setMessages([]);
    setError(null);
  };

  const sendMessage = async (text: string) => {
    const message = text.trim();
    if (!message || sending) return;

    setSending(true);
    setError(null);
    setInput("");

    const optimisticUser: AssistantMessage = {
      id: Date.now(),
      conversation_id: activeConversationId ?? 0,
      role: "user",
      content: message,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUser]);

    try {
      const response = await api.chatWithAssistant(message, activeConversationId ?? undefined);
      setActiveConversationId(response.conversation.id);
      setMessages((prev) => {
        const withoutOptimistic = prev.filter((m) => m.id !== optimisticUser.id);
        return [...withoutOptimistic, response.user_message, response.assistant_message];
      });
      reloadConversations();
    } catch (err) {
      setMessages((prev) => prev.filter((m) => m.id !== optimisticUser.id));
      setInput(message);
      setError(err instanceof Error ? err.message : "Could not reach the assistant");
    } finally {
      setSending(false);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleBriefing = async () => {
    if (sending) return;
    setSending(true);
    setError(null);
    try {
      const response = await api.getAssistantBriefing(activeConversationId ?? undefined);
      setActiveConversationId(response.conversation.id);
      setMessages(await api.getAssistantMessages(response.conversation.id));
      reloadConversations();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate briefing");
    } finally {
      setSending(false);
    }
  };

  const handleDeleteConversation = async (conversation: AssistantConversation) => {
    if (!confirm(`Delete "${conversation.title}"?`)) return;
    await api.deleteAssistantConversation(conversation.id);
    if (activeConversationId === conversation.id) {
      setActiveConversationId(null);
      setMessages([]);
    }
    reloadConversations();
  };

  return (
    <>
      <PageHeader
        title="AI Secretary"
        description={
          status?.configured
            ? `${status.name} helps you prioritize, summarize, and draft communications.`
            : "Add OPENAI_API_KEY to organizer/backend/.env to enable your AI secretary."
        }
      />

      {!statusLoading && !status?.configured && (
        <div className="error-banner">
          AI assistant not configured. Add <code>OPENAI_API_KEY</code> to{" "}
          <code>organizer/backend/.env</code> and restart the backend.
        </div>
      )}

      <div className="assistant-layout">
        <aside className="assistant-sidebar card">
          <div className="assistant-sidebar-header">
            <h3>Conversations</h3>
            <button className="btn btn-ghost" onClick={handleNewConversation} disabled={!status?.configured}>
              + New
            </button>
          </div>
          {conversationsLoading && <p className="meta">Loading...</p>}
          <div className="assistant-conversation-list">
            {conversations?.map((conversation) => (
              <button
                key={conversation.id}
                className={`assistant-conversation-item${
                  conversation.id === activeConversationId ? " active" : ""
                }`}
                onClick={() => setActiveConversationId(conversation.id)}
              >
                <span className="title">{conversation.title}</span>
                <span className="meta">{new Date(conversation.updated_at).toLocaleDateString()}</span>
              </button>
            ))}
          </div>
          {activeConversation && (
            <button
              className="btn btn-ghost assistant-delete"
              onClick={() => handleDeleteConversation(activeConversation)}
            >
              Delete conversation
            </button>
          )}
        </aside>

        <section className="assistant-chat card">
          <div className="assistant-chat-header">
            <div>
              <h3>{activeConversation?.title ?? `${status?.name ?? "Assistant"} is ready`}</h3>
              <p className="meta">
                {status?.configured
                  ? `Powered by ${status.model}`
                  : "Configure OpenAI to start chatting"}
              </p>
            </div>
            <button
              className="btn btn-primary"
              onClick={handleBriefing}
              disabled={!status?.configured || sending}
            >
              Morning briefing
            </button>
          </div>

          <div className="assistant-quick-actions">
            {QUICK_ACTIONS.map((action) => (
              <button
                key={action}
                className="assistant-chip"
                onClick={() => sendMessage(action)}
                disabled={!status?.configured || sending}
              >
                {action}
              </button>
            ))}
          </div>

          <div className="assistant-messages">
            {messages.length === 0 && !sending && (
              <div className="assistant-empty">
                <p>Ask {status?.name ?? "your assistant"} anything about your projects and communications.</p>
                <p className="meta">
                  Try the morning briefing or a quick action above to get started.
                </p>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`assistant-message assistant-message-${message.role}`}
              >
                <div className="assistant-message-label">
                  {message.role === "assistant" ? status?.name ?? "Assistant" : "You"}
                </div>
                <div className="assistant-message-body">{message.content}</div>
              </div>
            ))}

            {sending && (
              <div className="assistant-message assistant-message-assistant">
                <div className="assistant-message-label">{status?.name ?? "Assistant"}</div>
                <div className="assistant-message-body assistant-typing">Thinking...</div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {error && <div className="error-banner">{error}</div>}

          <form className="assistant-input-row" onSubmit={handleSubmit}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`Message ${status?.name ?? "your assistant"}...`}
              rows={2}
              disabled={!status?.configured || sending}
            />
            <button className="btn btn-primary" type="submit" disabled={!status?.configured || sending || !input.trim()}>
              Send
            </button>
          </form>
        </section>
      </div>
    </>
  );
}
