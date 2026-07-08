import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { PageHeader, useAsyncData } from "../components/ui";
import type { ChecklistItem } from "../types";

const PRIORITY_LABELS: Record<string, string> = {
  high: "Must do today",
  medium: "Today",
  low: "If time",
};

export default function DashboardPage() {
  const { data: stats } = useAsyncData(() => api.getStats());
  const { data: assistantStatus } = useAsyncData(() => api.getAssistantStatus());
  const {
    data: dayPlan,
    loading,
    error,
    reload,
  } = useAsyncData(() => api.getDayPlan());

  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);
  const [newItem, setNewItem] = useState("");
  const [addingItem, setAddingItem] = useState(false);

  const handleGenerate = async (regenerate = false) => {
    setGenerating(true);
    setGenError(null);
    try {
      await api.generateDayPlan(regenerate);
      reload();
    } catch (err) {
      setGenError(err instanceof Error ? err.message : "Could not generate your day plan");
    } finally {
      setGenerating(false);
    }
  };

  const handleToggleItem = async (item: ChecklistItem) => {
    await api.updateChecklistItem(item.id, { is_completed: !item.is_completed });
    reload();
  };

  const handleAddItem = async (e: FormEvent) => {
    e.preventDefault();
    if (!newItem.trim()) return;
    setAddingItem(true);
    try {
      await api.addChecklistItem(newItem.trim());
      setNewItem("");
      reload();
    } finally {
      setAddingItem(false);
    }
  };

  const completedCount = dayPlan?.checklist_items.filter((i) => i.is_completed).length ?? 0;
  const totalCount = dayPlan?.checklist_items.length ?? 0;
  const todayLabel = new Date().toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  });

  return (
    <>
      <PageHeader
        title="Start My Day"
        description={todayLabel}
      />

      {!assistantStatus?.configured && (
        <div className="error-banner">
          Add <code>OPENAI_API_KEY</code> to enable your daily brief and checklist.
        </div>
      )}

      <div className="day-start-hero card">
        <div className="day-start-hero-top">
          <div>
            <h3>Good morning</h3>
            <p className="meta">
              {dayPlan
                ? `Your plan was prepared at ${new Date(dayPlan.generated_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`
                : "Generate a brief for today, this week, and this month — plus a checklist to work through."}
            </p>
          </div>
          <div className="day-start-actions">
            {!dayPlan ? (
              <button
                className="btn btn-primary"
                onClick={() => handleGenerate(false)}
                disabled={!assistantStatus?.configured || generating}
              >
                {generating ? "Preparing..." : "Start my day"}
              </button>
            ) : (
              <button
                className="btn btn-ghost"
                onClick={() => handleGenerate(true)}
                disabled={generating}
              >
                {generating ? "Refreshing..." : "Refresh brief"}
              </button>
            )}
          </div>
        </div>

        {genError && <div className="error-banner">{genError}</div>}
        {error && <div className="error-banner">{error}</div>}
        {loading && <p className="meta">Loading your day...</p>}

        {dayPlan?.greeting && <p className="day-greeting">{dayPlan.greeting}</p>}
      </div>

      {dayPlan && (
        <>
          <div className="day-focus-grid">
            <FocusCard title="Today" items={dayPlan.today_focus} accent="today" />
            <FocusCard title="This week" items={dayPlan.week_focus} accent="week" />
            <FocusCard title="This month" items={dayPlan.month_focus} accent="month" />
          </div>

          <div className="card day-checklist-card">
            <div className="day-checklist-header">
              <div>
                <h3>Today's checklist</h3>
                <p className="meta">
                  {completedCount} of {totalCount} done
                  {totalCount > 0 && (
                    <span className="day-progress">
                      {" "}
                      · {Math.round((completedCount / totalCount) * 100)}%
                    </span>
                  )}
                </p>
              </div>
            </div>

            {totalCount > 0 && (
              <div className="day-progress-bar">
                <div
                  className="day-progress-fill"
                  style={{ width: `${totalCount ? (completedCount / totalCount) * 100 : 0}%` }}
                />
              </div>
            )}

            <ul className="day-checklist">
              {dayPlan.checklist_items.map((item) => (
                <li key={item.id} className={item.is_completed ? "completed" : undefined}>
                  <label>
                    <input
                      type="checkbox"
                      checked={item.is_completed}
                      onChange={() => handleToggleItem(item)}
                    />
                    <span className="checklist-text">{item.text}</span>
                    <span className={`badge badge-priority badge-priority-${item.priority}`}>
                      {PRIORITY_LABELS[item.priority] ?? item.priority}
                    </span>
                  </label>
                </li>
              ))}
            </ul>

            <form className="day-add-item" onSubmit={handleAddItem}>
              <input
                value={newItem}
                onChange={(e) => setNewItem(e.target.value)}
                placeholder="Add your own task..."
                disabled={addingItem}
              />
              <button className="btn btn-primary" type="submit" disabled={addingItem || !newItem.trim()}>
                Add
              </button>
            </form>
          </div>
        </>
      )}

      {stats && (
        <div className="day-stats-section">
          <h3 className="section-title">At a glance</h3>
          <div className="stats-grid">
            {[
              { label: "Active projects", value: stats.active_projects },
              { label: "Unread emails", value: stats.unread_emails },
              { label: "Unread texts", value: stats.unread_texts },
              { label: "Voicemails", value: stats.unlistened_voicemails },
            ].map((card) => (
              <div key={card.label} className="stat-card">
                <div className="label">{card.label}</div>
                <div className="value">{card.value}</div>
              </div>
            ))}
          </div>
          <p className="meta" style={{ marginTop: "1rem" }}>
            Need more detail? Talk to <Link to="/assistant">{assistantStatus?.name ?? "your assistant"}</Link> or
            check <Link to="/integrations">Integrations</Link> to sync latest data.
          </p>
        </div>
      )}
    </>
  );
}

function FocusCard({
  title,
  items,
  accent,
}: {
  title: string;
  items: string[];
  accent: string;
}) {
  return (
    <div className={`card focus-card focus-card-${accent}`}>
      <h3>{title}</h3>
      {items.length === 0 ? (
        <p className="meta">Nothing flagged right now.</p>
      ) : (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
