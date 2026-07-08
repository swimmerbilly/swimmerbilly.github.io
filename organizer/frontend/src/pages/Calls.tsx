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
import type { CommunicationDirection } from "../types";

export default function CallsPage() {
  const { data: calls, error, loading, reload } = useAsyncData(() => api.getCalls());
  const [showModal, setShowModal] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState("");
  const [contactName, setContactName] = useState("");
  const [durationSeconds, setDurationSeconds] = useState("");
  const [notes, setNotes] = useState("");
  const [direction, setDirection] = useState<CommunicationDirection>("inbound");

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    await api.createCall({
      project_id: null,
      direction,
      contact_name: contactName || null,
      phone_number: phoneNumber,
      duration_seconds: durationSeconds ? parseInt(durationSeconds, 10) : null,
      notes: notes || null,
    });
    setShowModal(false);
    setPhoneNumber("");
    setContactName("");
    setDurationSeconds("");
    setNotes("");
    reload();
  };

  return (
    <>
      <PageHeader title="Calls" description="Log phone calls and keep notes on conversations." />

      <div className="toolbar">
        <span>{calls?.length ?? 0} calls</span>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          + Log Call
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {loading && <p>Loading calls...</p>}

      {!loading && calls?.length === 0 && (
        <EmptyState
          message="No calls logged yet."
          action={
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>
              Log your first call
            </button>
          }
        />
      )}

      <div className="list">
        {calls?.map((call) => (
          <div key={call.id} className="list-item">
            <div>
              <div className="title">
                {call.contact_name || call.phone_number}
                <span className="meta" style={{ marginLeft: "0.5rem" }}>
                  ({call.direction})
                </span>
              </div>
              <div className="meta">
                Duration: {formatDuration(call.duration_seconds)} · {formatDate(call.called_at)}
              </div>
              {call.notes && <p style={{ marginTop: "0.5rem" }}>{call.notes}</p>}
            </div>
          </div>
        ))}
      </div>

      <Modal title="Log Call" isOpen={showModal} onClose={() => setShowModal(false)}>
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
          <FormField label="Duration (seconds)">
            <input
              type="number"
              value={durationSeconds}
              onChange={(e) => setDurationSeconds(e.target.value)}
              min="0"
            />
          </FormField>
          <FormField label="Notes">
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} />
          </FormField>
        </SubmitForm>
      </Modal>
    </>
  );
}
