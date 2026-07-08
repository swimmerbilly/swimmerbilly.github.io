import { useMemo, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import ProjectLinkBar from "../components/ProjectLinkBar";
import UnlinkedFilter from "../components/UnlinkedFilter";
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
  const [unlinkedOnly, setUnlinkedOnly] = useState(false);
  const { data: emails, error, loading, reload } = useAsyncData(
    () => api.getEmails({ unlinkedOnly }),
    [unlinkedOnly]
  );
  const { data: projects } = useAsyncData(() => api.getProjects());
  const { data: allEmails, reload: reloadAllEmails } = useAsyncData(() => api.getEmails());

  const refresh = () => {
    reload();
    reloadAllEmails();
  };

  const unlinkedCount = useMemo(
    () => allEmails?.filter((e) => !e.project_id).length ?? 0,
    [allEmails]
  );

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
    refresh();
  };

  const toggleRead = async (id: number, isRead: boolean) => {
    await api.updateEmail(id, { is_read: !isRead });
    refresh();
  };

  return (
    <>
      <PageHeader
        title="Emails"
        description="Link emails to Harvest projects so your timeline and briefs stay accurate."
      />

      <div className="toolbar">
        <span>
          {emails?.length ?? 0} emails
          {unlinkedCount > 0 && !unlinkedOnly && (
            <span className="meta"> · {unlinkedCount} unlinked</span>
          )}
        </span>
        <div className="toolbar-actions">
          <UnlinkedFilter
            showUnlinkedOnly={unlinkedOnly}
            onChange={setUnlinkedOnly}
            unlinkedCount={unlinkedCount}
          />
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            + Log Email
          </button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {loading && <p>Loading emails...</p>}

      {!loading && emails?.length === 0 && (
        <EmptyState
          message={
            unlinkedOnly
              ? "All emails are linked to projects."
              : "No emails logged yet."
          }
          action={
            !unlinkedOnly ? (
              <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                Log your first email
              </button>
            ) : undefined
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
                {!email.project_id && <span className="badge badge-unlinked">Unlinked</span>}
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
              {projects && (
                <ProjectLinkBar
                  commType="email"
                  commId={email.id}
                  projectId={email.project_id}
                  projectName={email.project_name}
                  projectColor={email.project_color}
                  projects={projects}
                  onUpdated={refresh}
                />
              )}
              <div className="comm-actions" onClick={(e) => e.stopPropagation()}>
                <Link className="btn btn-ghost btn-sm" to={`/assistant?email_id=${email.id}`}>
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
