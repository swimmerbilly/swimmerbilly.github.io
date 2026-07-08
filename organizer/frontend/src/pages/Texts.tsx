import { useMemo, useState, type FormEvent } from "react";
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

export default function TextsPage() {
  const [unlinkedOnly, setUnlinkedOnly] = useState(false);
  const { data: texts, error, loading, reload } = useAsyncData(
    () => api.getTexts({ unlinkedOnly }),
    [unlinkedOnly]
  );
  const { data: projects } = useAsyncData(() => api.getProjects());
  const { data: allTexts, reload: reloadAllTexts } = useAsyncData(() => api.getTexts());

  const refresh = () => {
    reload();
    reloadAllTexts();
  };

  const unlinkedCount = useMemo(
    () => allTexts?.filter((t) => !t.project_id).length ?? 0,
    [allTexts]
  );

  const [showModal, setShowModal] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState("");
  const [contactName, setContactName] = useState("");
  const [body, setBody] = useState("");
  const [direction, setDirection] = useState<CommunicationDirection>("inbound");

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    await api.createText({
      project_id: null,
      direction,
      contact_name: contactName || null,
      phone_number: phoneNumber,
      body,
      is_read: false,
    });
    setShowModal(false);
    setPhoneNumber("");
    setContactName("");
    setBody("");
    refresh();
  };

  const toggleRead = async (id: number, isRead: boolean) => {
    await api.updateText(id, { is_read: !isRead });
    refresh();
  };

  return (
    <>
      <PageHeader title="Texts" description="Link texts to the right Harvest project." />

      <div className="toolbar">
        <span>
          {texts?.length ?? 0} messages
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
            + Log Text
          </button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {loading && <p>Loading texts...</p>}

      {!loading && texts?.length === 0 && (
        <EmptyState
          message={
            unlinkedOnly ? "All texts are linked to projects." : "No text messages logged yet."
          }
        />
      )}

      <div className="list">
        {texts?.map((text) => (
          <div
            key={text.id}
            className={`list-item${text.is_read ? "" : " unread"}`}
            onClick={() => toggleRead(text.id, text.is_read)}
            style={{ cursor: "pointer" }}
          >
            <div>
              <div className="title">
                {text.contact_name || text.phone_number}
                <span className="meta" style={{ marginLeft: "0.5rem" }}>
                  ({text.direction})
                </span>
                {!text.project_id && <span className="badge badge-unlinked">Unlinked</span>}
              </div>
              <p style={{ marginTop: "0.35rem" }}>{text.body}</p>
              <div className="meta">{formatDate(text.sent_at)}</div>
              {projects && (
                <ProjectLinkBar
                  commType="text"
                  commId={text.id}
                  projectId={text.project_id}
                  projectName={text.project_name}
                  projectColor={text.project_color}
                  projects={projects}
                  onUpdated={refresh}
                />
              )}
            </div>
          </div>
        ))}
      </div>

      <Modal title="Log Text Message" isOpen={showModal} onClose={() => setShowModal(false)}>
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
          <FormField label="Contact Name">
            <input value={contactName} onChange={(e) => setContactName(e.target.value)} />
          </FormField>
          <FormField label="Phone Number">
            <input value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} required />
          </FormField>
          <FormField label="Message">
            <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={3} required />
          </FormField>
        </SubmitForm>
      </Modal>
    </>
  );
}
