import { useCallback, useEffect, useMemo, useState } from "react";
import { listTickets, updateStatus } from "../api.js";
import { CATEGORY_LABELS, PRIORITY_LABELS, STATUS_LABELS, label } from "../constants.js";
import { TicketDetail } from "./AnalysisResult.jsx";

function StatsCards({ tickets }) {
  const stats = [
    ["Total", tickets.length],
    ["Open", tickets.filter((t) => t.status === "open").length],
    ["High / Urgent", tickets.filter((t) => t.priority === "high" || t.priority === "urgent").length],
    ["Resolved", tickets.filter((t) => t.status === "resolved").length],
  ];
  return (
    <div className="stats">
      {stats.map(([name, value]) => (
        <div className="stat" key={name}>
          <span className="stat-value">{value}</span>
          <span className="stat-name">{name}</span>
        </div>
      ))}
    </div>
  );
}

export default function Dashboard({ onNewReport }) {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [statusFilter, setStatusFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setTickets(await listTickets());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const visible = useMemo(
    () => tickets.filter((t) =>
      (statusFilter === "all" || t.status === statusFilter) &&
      (priorityFilter === "all" || t.priority === priorityFilter)),
    [tickets, statusFilter, priorityFilter]
  );
  const selected = tickets.find((t) => t.id === selectedId) || null;

  async function changeStatus(status) {
    setSaving(true);
    setSaveError("");
    try {
      const updated = await updateStatus(selected.id, status);
      setTickets((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
    } catch (err) {
      setSaveError(err.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p className="panel" role="status">Loading tickets…</p>;
  if (error) {
    return (
      <div className="panel">
        <p className="banner banner-error" role="alert">{error}</p>
        <button className="btn-primary" onClick={load}>Try again</button>
      </div>
    );
  }
  if (tickets.length === 0) {
    return (
      <div className="panel">
        <h2>No tickets yet</h2>
        <p>Reports will appear here once someone submits one.</p>
        <button className="btn-primary" onClick={onNewReport}>Create a report</button>
      </div>
    );
  }

  return (
    <section>
      <StatsCards tickets={tickets} />

      <div className="filters">
        <label>
          Status{" "}
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="all">All</option>
            {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </label>
        <label>
          Priority{" "}
          <select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)}>
            <option value="all">All</option>
            {Object.entries(PRIORITY_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </label>
        <button className="btn-secondary" onClick={load}>Refresh</button>
      </div>

      <div className="dash-grid">
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>#</th><th>Title</th><th>Location</th><th>Category</th><th>Priority</th><th>Status</th></tr>
            </thead>
            <tbody>
              {visible.length === 0 && (
                <tr><td colSpan={6}>No tickets match these filters.</td></tr>
              )}
              {visible.map((t) => (
                <tr
                  key={t.id} tabIndex={0}
                  className={t.id === selectedId ? "row selected" : "row"}
                  onClick={() => setSelectedId(t.id)}
                  onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && setSelectedId(t.id)}
                >
                  <td>{t.id}</td>
                  <td>{t.title}</td>
                  <td>{t.location}</td>
                  <td>{label(CATEGORY_LABELS, t.category)}</td>
                  <td><span className={`badge prio-${t.priority}`}>{label(PRIORITY_LABELS, t.priority)}</span></td>
                  <td>{label(STATUS_LABELS, t.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <aside className="panel side" aria-live="polite">
          {!selected && <p>Select a ticket to see details.</p>}
          {selected && (
            <>
              <label htmlFor="status-select">Update status</label>
              <select
                id="status-select" value={selected.status} disabled={saving}
                onChange={(e) => changeStatus(e.target.value)}
              >
                {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
              {saveError && <p className="field-error" role="alert">{saveError}</p>}
              <TicketDetail ticket={selected} />
            </>
          )}
        </aside>
      </div>
    </section>
  );
}
