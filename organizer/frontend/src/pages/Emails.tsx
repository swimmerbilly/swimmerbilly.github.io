import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import ProjectLinkSuggest from "../components/ProjectLinkSuggest";
import {
  EmptyState,
  FormField,
  Modal,
  PageHeader,
  SubmitForm,
  formatDate,
  useAsyncData,
} from "../components/ui";
import type { CommunicationDirection } from "../types";

export default function EmailsPage() {
  const { data: emails, error, loading, reload } = useAsyncData(() => api.getEmails());
  const [showModal, setShowModal] = useState(false);
  const [fromAddress, setFromAddress] = useState("");
  const [toAddress, setToAddress] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [direction, setDirection] = useState<CommunicationDirection>("inbound");

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    await api.createEmail({
      project_id: null,
      direction,
      from_address: fromAddress,
      to_address: toAddress,
      subject,
      body,
      is_read: false,
      is_starred: false,
    });
    setShowModal(false);
    setFromAddress("");
    setToAddress("");
    setSubject("");
    setBody("");
    reload();
  };

  const toggleRead = async (id: number, isRead: boolean) => {
    await api.updateEmail(id, { is_read: !isRead });
    reload();
  };

  return (
    <>
      <PageHeader
        title="Emails"
        description="Work Outlook and personal Gmail sync from Integrations. Manual entries are also supported."
      />

      <div className="toolbar">
        <span>{emails?.length ?? 0} emails</span>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          + Log Email
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {loading && <p>Loading emails...</p>}

      {!loading && emails?.length === 0 && (
        <EmptyState
          message="No emails logged yet."
          action={
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>
              Log your first email
            </button>
          }
        />
      )}

      <div className="list">
        {emails?.map((email) => (
          <div
            key={email.id}
            className={`list-item${email.is_read ? "" : " unread"}`}
            onClick={() => toggleRead(email.id, email.is_read)}
            style={{ cursor: "pointer" }}
          >
            <div>
              <div className="title">
                {email.subject || "(no subject)"}
                {email.account_label === "work" && <span className="badge badge-work">Outlook</span>}
                {email.account_label === "personal" && <span className="badge badge-personal">Gmail</span>}
              </div>
              <div className="meta">
                {email.direction === "inbound" ? "From" : "To"}:{" "}
                {email.direction === "inbound" ? email.from_address : email.to_address}
              </div>
              {email.body && (
                <p className="meta" style={{ marginTop: "0.5rem" }}>
                  {email.body.slice(0, 120)}
                  {email.body.length > 120 ? "…" : ""}
                </p>
              )}
              <div className="meta">{formatDate(email.received_at)}</div>
              <ProjectLinkSuggest
                commType="email"
                commId={email.id}
                projectId={email.project_id}
                onLinked={reload}
              />
              <div className="comm-actions" onClick={(e) => e.stopPropagation()}>
                <Link
                  className="btn btn-ghost btn-sm"
                  to={`/assistant?email_id=${email.id}`}
                >
                  Draft reply with Alex
                </Link>
              </div>
            </div>
            {email.is_starred && <span>★</span>}
          </div>
        ))}
      </div>

      <Modal title="Log Email" isOpen={showModal} onClose={() => setShowModal(false)}>
        <SubmitForm onSubmit={handleCreate} onCancel={() => setShowModal(false)}>
          <FormField label="Direction">
            <select
              value={direction}
              onChange={(e) => setDirection(e.target.value as CommunicationDirection)}
            >
              <option value="inbound">Inbound</option>
              <option value="outbound">Outbound</option>
            </select>
          </FormField>
          <FormField label="From">
            <input value={fromAddress} onChange={(e) => setFromAddress(e.target.value)} required />
          </FormField>
          <FormField label="To">
            <input value={toAddress} onChange={(e) => setToAddress(e.target.value)} required />
          </FormField>
          <FormField label="Subject">
            <input value={subject} onChange={(e) => setSubject(e.target.value)} />
          </FormField>
          <FormField label="Body">
            <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={4} />
          </FormField>
        </SubmitForm>
      </Modal>
    </>
  );
}
