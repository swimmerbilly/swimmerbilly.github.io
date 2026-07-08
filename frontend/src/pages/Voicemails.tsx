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
  formatDuration,
  useAsyncData,
} from "../components/ui";

export default function VoicemailsPage() {
  const [unlinkedOnly, setUnlinkedOnly] = useState(false);
  const { data: voicemails, error, loading, reload } = useAsyncData(
    () => api.getVoicemails({ unlinkedOnly }),
    [unlinkedOnly]
  );
  const { data: projects } = useAsyncData(() => api.getProjects());
  const { data: allVoicemails, reload: reloadAllVoicemails } = useAsyncData(() => api.getVoicemails());

  const refresh = () => {
    reload();
    reloadAllVoicemails();
  };

  const unlinkedCount = useMemo(
    () => allVoicemails?.filter((v) => !v.project_id).length ?? 0,
    [allVoicemails]
  );

  const [showModal, setShowModal] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState("");
  const [contactName, setContactName] = useState("");
  const [transcript, setTranscript] = useState("");
  const [durationSeconds, setDurationSeconds] = useState("");

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    await api.createVoicemail({
      project_id: null,
      contact_name: contactName || null,
      phone_number: phoneNumber,
      transcript: transcript || null,
      audio_path: null,
      duration_seconds: durationSeconds ? parseInt(durationSeconds, 10) : null,
      is_listened: false,
    });
    setShowModal(false);
    setPhoneNumber("");
    setContactName("");
    setTranscript("");
    setDurationSeconds("");
    refresh();
  };

  const toggleListened = async (id: number, isListened: boolean) => {
    await api.updateVoicemail(id, { is_listened: !isListened });
    refresh();
  };

  return (
    <>
      <PageHeader
        title="Voicemails"
        description="Link voicemails to projects so nothing falls through the cracks."
      />

      <div className="toolbar">
        <span>
          {voicemails?.length ?? 0} voicemails
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
            + Log Voicemail
          </button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {loading && <p>Loading voicemails...</p>}

      {!loading && voicemails?.length === 0 && (
        <EmptyState
          message={
            unlinkedOnly
              ? "All voicemails are linked to projects."
              : "No voicemails logged yet."
          }
        />
      )}

      <div className="list">
        {voicemails?.map((vm) => (
          <div
            key={vm.id}
            className={`list-item${vm.is_listened ? "" : " unread"}`}
            onClick={() => toggleListened(vm.id, vm.is_listened)}
            style={{ cursor: "pointer" }}
          >
            <div>
              <div className="title">
                {vm.contact_name || vm.phone_number}
                {vm.grasshopper_message_id && (
                  <span className="badge badge-grasshopper">Grasshopper</span>
                )}
                {!vm.project_id && <span className="badge badge-unlinked">Unlinked</span>}
              </div>
              <div className="meta">
                Duration: {formatDuration(vm.duration_seconds)} · {formatDate(vm.received_at)}
              </div>
              {vm.audio_path && (
                <audio
                  controls
                  src={vm.audio_path}
                  style={{ marginTop: "0.75rem", width: "100%" }}
                  onClick={(e) => e.stopPropagation()}
                />
              )}
              {vm.transcript && (
                <p style={{ marginTop: "0.5rem" }}>
                  {vm.transcript.slice(0, 150)}
                  {vm.transcript.length > 150 ? "…" : ""}
                </p>
              )}
              {projects && (
                <ProjectLinkBar
                  commType="voicemail"
                  commId={vm.id}
                  projectId={vm.project_id}
                  projectName={vm.project_name}
                  projectColor={vm.project_color}
                  projects={projects}
                  onUpdated={refresh}
                />
              )}
            </div>
          </div>
        ))}
      </div>

      <Modal title="Log Voicemail" isOpen={showModal} onClose={() => setShowModal(false)}>
        <SubmitForm onSubmit={handleCreate} onCancel={() => setShowModal(false)}>
          <FormField label="Contact Name">
            <input value={contactName} onChange={(e) => setContactName(e.target.value)} />
          </FormField>
          <FormField label="Phone Number">
            <input value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} required />
          </FormField>
          <FormField label="Duration (seconds)">
            <input
              type="number"
              value={durationSeconds}
              onChange={(e) => setDurationSeconds(e.target.value)}
              min="0"
            />
          </FormField>
          <FormField label="Transcript">
            <textarea value={transcript} onChange={(e) => setTranscript(e.target.value)} rows={4} />
          </FormField>
        </SubmitForm>
      </Modal>
    </>
  );
}
