import { useState, type FormEvent } from "react";
import { api } from "../api/client";
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
  const { data: voicemails, error, loading, reload } = useAsyncData(() =>
    api.getVoicemails()
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
    reload();
  };

  const toggleListened = async (id: number, isListened: boolean) => {
    await api.updateVoicemail(id, { is_listened: !isListened });
    reload();
  };

  return (
    <>
      <PageHeader
        title="Voicemails"
        description="Track voicemails and transcripts in one place."
      />

      <div className="toolbar">
        <span>{voicemails?.length ?? 0} voicemails</span>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          + Log Voicemail
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {loading && <p>Loading voicemails...</p>}

      {!loading && voicemails?.length === 0 && (
        <EmptyState
          message="No voicemails logged yet."
          action={
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>
              Log your first voicemail
            </button>
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
              <div className="title">{vm.contact_name || vm.phone_number}</div>
              <div className="meta">
                Duration: {formatDuration(vm.duration_seconds)} · {formatDate(vm.received_at)}
              </div>
              {vm.transcript && (
                <p style={{ marginTop: "0.5rem" }}>
                  {vm.transcript.slice(0, 150)}
                  {vm.transcript.length > 150 ? "…" : ""}
                </p>
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
