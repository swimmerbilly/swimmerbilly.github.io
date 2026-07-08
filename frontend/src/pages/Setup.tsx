import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { PageHeader, useAsyncData } from "../components/ui";
import type { SetupField, SetupStep } from "../types";

export default function SetupPage() {
  const { data: status, loading, error, reload } = useAsyncData(() => api.getSetupStatus());
  const [activeStep, setActiveStep] = useState<string | null>(null);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveOk, setSaveOk] = useState(false);

  const openStep = (step: SetupStep) => {
    setActiveStep(step.id);
    setSaveError(null);
    setSaveOk(false);
    const initial: Record<string, string> = {};
    for (const field of step.fields) {
      initial[field.key] = field.secret && field.has_value ? "" : (field.value ?? "");
    }
    setFormValues(initial);
  };

  const handleSave = async (stepId: string) => {
    setSaving(true);
    setSaveError(null);
    setSaveOk(false);
    try {
      await api.saveSetupStep(stepId, formValues);
      setSaveOk(true);
      reload();
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Could not save");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="meta">Loading setup...</p>;

  return (
    <>
      <PageHeader
        title="Connect your accounts"
        description="Enter credentials here — no need to edit .env by hand. Secrets are stored locally in your database."
      />

      {error && <div className="error-banner">{error}</div>}

      {status && !status.required_configured && (
        <div className="card setup-banner">
          <p>
            <strong>Almost there.</strong> Connect Harvest, work Outlook, and Alex to unlock Start My Day
            and your full workflow. Gmail and Grasshopper are optional.
          </p>
        </div>
      )}

      {status?.required_configured && (
        <div className="card setup-banner setup-banner-ok">
          <p>
            <strong>Core integrations connected.</strong> Head to{" "}
            <Link to="/integrations">Integrations</Link> to sync data, or{" "}
            <Link to="/">Start My Day</Link>.
          </p>
        </div>
      )}

      <div className="setup-steps-list">
        {status?.steps.map((step) => (
          <div key={step.id} className={`card setup-step-card${step.configured ? " configured" : ""}`}>
            <div className="setup-step-header">
              <div>
                <h3>
                  {step.title}
                  {step.configured && <span className="badge badge-active">Connected</span>}
                  {step.optional && !step.configured && (
                    <span className="badge badge-on_hold">Optional</span>
                  )}
                </h3>
                <p className="meta">{step.description}</p>
                {step.help_text && <p className="meta">{step.help_text}</p>}
                {step.help_url && (
                  <p className="meta">
                    <a href={step.help_url} target="_blank" rel="noreferrer">
                      Get credentials →
                    </a>
                  </p>
                )}
              </div>
              <button className="btn btn-ghost" onClick={() => openStep(step)}>
                {step.configured ? "Update" : "Set up"}
              </button>
            </div>

            {activeStep === step.id && (
              <form
                className="setup-form"
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSave(step.id);
                }}
              >
                {step.fields.map((field: SetupField) => (
                  <label key={field.key} className="setup-field">
                    <span>{field.label}</span>
                    <input
                      type={field.secret ? "password" : "text"}
                      value={formValues[field.key] ?? ""}
                      onChange={(e) =>
                        setFormValues((prev) => ({ ...prev, [field.key]: e.target.value }))
                      }
                      placeholder={
                        field.secret && field.has_value
                          ? `Saved ${field.masked ?? "••••"} — leave blank to keep`
                          : field.placeholder || field.label
                      }
                      autoComplete="off"
                    />
                  </label>
                ))}
                {saveError && <div className="error-banner">{saveError}</div>}
                {saveOk && <p className="sync-result">Saved. You can sync from Integrations now.</p>}
                <div className="setup-form-actions">
                  <button type="button" className="btn btn-ghost" onClick={() => setActiveStep(null)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary" disabled={saving}>
                    {saving ? "Saving..." : "Save"}
                  </button>
                </div>
              </form>
            )}
          </div>
        ))}
      </div>
    </>
  );
}
