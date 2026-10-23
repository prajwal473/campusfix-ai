import { CATEGORY_LABELS, PRIORITY_LABELS, STATUS_LABELS, VERIFICATION_LABELS, label } from "../constants.js";
import { imageSrc } from "../api.js";

function List({ title, items }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="block">
      <h4>{title}</h4>
      <ul>{items.map((t, i) => <li key={i}>{t}</li>)}</ul>
    </div>
  );
}

// Shared by the result screen and the dashboard detail panel.
export function TicketDetail({ ticket }) {
  const aiFailed = ticket.ai_status && ticket.ai_status !== "ok";
  return (
    <div className="detail">
      {aiFailed && (
        <p className="banner banner-warn" role="status">
          AI analysis was unavailable for this report. The category and priority below are placeholders,
          so staff must review it.
        </p>
      )}

      <h3>{ticket.title}</h3>
      <p className="meta">
        Ticket #{ticket.id} · {ticket.location} · Status: {label(STATUS_LABELS, ticket.status)}
      </p>

      <div className="badges">
        <span className="badge">{label(CATEGORY_LABELS, ticket.category)}</span>
        <span className={`badge prio-${ticket.priority}`}>Suggested priority: {label(PRIORITY_LABELS, ticket.priority)}</span>
        <span className={`badge ver-${ticket.verification_status}`}>{label(VERIFICATION_LABELS, ticket.verification_status)}</span>
      </div>

      {ticket.image_url && (
        <div className="block">
          <img className="ticket-img" src={imageSrc(ticket.image_url)} alt="Photo attached to this report" />
          {!ticket.image_analyzed && (
            <p className="note">This photo was attached for staff but was not analysed by the model.</p>
          )}
        </div>
      )}

      <div className="block">
        <h4>Why this priority</h4>
        <p>{ticket.priority_reason}</p>
      </div>

      <List title="What the evidence shows" items={ticket.observations} />
      <List title="What is assumed, not confirmed" items={ticket.assumptions} />

      {ticket.evidence_summary && (
        <div className="block">
          <h4>Evidence summary</h4>
          <p>{ticket.evidence_summary}</p>
        </div>
      )}

      <div className="block">
        <h4>Recommended next step</h4>
        <p>{ticket.recommended_next_step}</p>
      </div>

      <List title="Questions for the reporter" items={ticket.missing_information} />

      <p className="note">
        {ticket.ai_provider ? `Analysed with ${ticket.ai_provider}. ` : ""}
        AI output is a suggestion for staff review, not an emergency assessment. If someone may be in danger,
        keep clear of the area and contact campus staff or emergency services.
      </p>
    </div>
  );
}

export default function AnalysisResult({ ticket, onNew, onDashboard }) {
  return (
    <section className="panel">
      <h2>Report received</h2>
      <p className="ticket-id">Your ticket number is #{ticket.id}</p>
      <TicketDetail ticket={ticket} />
      <div className="actions">
        <button className="btn-primary" onClick={onDashboard}>Open dashboard</button>
        <button className="btn-secondary" onClick={onNew}>Report another problem</button>
      </div>
    </section>
  );
}
