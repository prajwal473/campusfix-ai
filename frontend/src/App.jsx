import { useState } from "react";
import ReportForm from "./components/ReportForm.jsx";
import AnalysisResult from "./components/AnalysisResult.jsx";
import Dashboard from "./components/Dashboard.jsx";

export default function App() {
  const [view, setView] = useState("report"); // "report" | "result" | "dashboard"
  const [ticket, setTicket] = useState(null);

  return (
    <div className="app">
      <header className="top">
        <div>
          <h1>CampusFix AI</h1>
          <p className="tagline">Turn campus problems into actionable reports.</p>
        </div>
        <nav aria-label="Main">
          <button className={view !== "dashboard" ? "tab active" : "tab"} onClick={() => setView("report")}>
            Report
          </button>
          <button className={view === "dashboard" ? "tab active" : "tab"} onClick={() => setView("dashboard")}>
            Staff dashboard
          </button>
        </nav>
      </header>

      <main>
        {view === "report" && (
          <ReportForm onCreated={(t) => { setTicket(t); setView("result"); }} />
        )}
        {view === "result" && ticket && (
          <AnalysisResult ticket={ticket} onNew={() => setView("report")} onDashboard={() => setView("dashboard")} />
        )}
        {view === "dashboard" && <Dashboard onNewReport={() => setView("report")} />}
      </main>

      <footer>
        Priorities and categories are AI suggestions for staff review. Demo mode: no sign-in is required.
      </footer>
    </div>
  );
}
