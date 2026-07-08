import { api } from "../api/client";
import { EmptyState, PageHeader, useAsyncData } from "../components/ui";

export default function DashboardPage() {
  const { data: stats, error, loading } = useAsyncData(() => api.getStats());

  if (loading) return <p>Loading dashboard...</p>;
  if (error) return <div className="error-banner">{error}</div>;
  if (!stats) return null;

  const statCards = [
    { label: "Active Projects", value: stats.active_projects },
    { label: "Unread Emails", value: stats.unread_emails },
    { label: "Unread Texts", value: stats.unread_texts },
    { label: "Unlistened Voicemails", value: stats.unlistened_voicemails },
    { label: "Calls This Week", value: stats.recent_calls },
    { label: "Total Communications", value: stats.total_communications },
  ];

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Your unified view of projects and communications."
      />

      <div className="stats-grid">
        {statCards.map((card) => (
          <div key={card.label} className="stat-card">
            <div className="label">{card.label}</div>
            <div className="value">{card.value}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <h3 style={{ marginBottom: "0.5rem" }}>Getting Started</h3>
        <p style={{ color: "var(--text-muted)", marginBottom: "1rem" }}>
          Life Organizer helps you track projects alongside emails, texts, calls,
          and voicemails in one place. Start by creating a project, then log your
          communications and link them to projects as you go.
        </p>
        {stats.project_count === 0 && (
          <EmptyState message="No projects yet — head to Projects to create your first one." />
        )}
      </div>
    </>
  );
}
