import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import CallsPage from "./pages/Calls";
import DashboardPage from "./pages/Dashboard";
import EmailsPage from "./pages/Emails";
import IntegrationsPage from "./pages/Integrations";
import ProjectsPage from "./pages/Projects";
import TextsPage from "./pages/Texts";
import VoicemailsPage from "./pages/Voicemails";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="integrations" element={<IntegrationsPage />} />
        <Route path="emails" element={<EmailsPage />} />
        <Route path="texts" element={<TextsPage />} />
        <Route path="calls" element={<CallsPage />} />
        <Route path="voicemails" element={<VoicemailsPage />} />
      </Route>
    </Routes>
  );
}
