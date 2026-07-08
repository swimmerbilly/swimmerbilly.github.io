import { NavLink, Outlet } from "react-router-dom";
import { NotepadProvider } from "./NotepadProvider";

const navItems = [
  { to: "/", label: "Start My Day", icon: "☀" },
  { to: "/projects", label: "Projects", icon: "▣" },
  { to: "/integrations", label: "Integrations", icon: "⚡" },
  { to: "/assistant", label: "Assistant", icon: "✦" },
  { to: "/emails", label: "Emails", icon: "✉" },
  { to: "/texts", label: "Texts", icon: "💬" },
  { to: "/calls", label: "Calls", icon: "📞" },
  { to: "/voicemails", label: "Voicemails", icon: "🔊" },
];

export default function Layout() {
  return (
    <NotepadProvider>
      <div className="app-layout">
        <aside className="sidebar">
          <div className="brand">
            <div className="brand-icon">LO</div>
            <h1>Life Organizer</h1>
          </div>
          <nav className="nav">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) => (isActive ? "active" : undefined)}
              >
                <span>{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </nav>
        </aside>
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </NotepadProvider>
  );
}
