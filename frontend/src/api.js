const BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

// DEV ONLY: set to true only while the backend is not ready. Never use for the demo.
export const USE_MOCKS = false;
const DEV_SAMPLE = [
  {
    id: 0, title: "DEV SAMPLE (not a real report)", description: "Development placeholder.",
    location: "n/a", category: "other", priority: "low", priority_reason: "Placeholder.",
    evidence_summary: "Placeholder.", verification_status: "not_assessed",
    recommended_next_step: "n/a", status: "open", image_url: null, ai_provider: null,
    created_at: new Date().toISOString(), ai_status: "not_run",
    observations: [], assumptions: [], image_analyzed: false,
  },
];

export function imageSrc(path) {
  return path ? `${BASE}${path}` : null;
}

// FastAPI returns detail as a string (404/413/415) or a list (422). Handle both.
function readDetail(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : "";
        return field && field !== "body" ? `${field}: ${d.msg}` : d.msg;
      })
      .join(" ");
  }
  return "Something went wrong. Please try again.";
}

async function request(path, options) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, options);
  } catch {
    throw new Error("Cannot reach the server. Check that the backend is running.");
  }
  if (!res.ok) {
    let body = null;
    try { body = await res.json(); } catch { /* ignore */ }
    throw new Error(readDetail(body?.detail));
  }
  return res.json();
}

export const createTicket = (formData) =>
  request("/api/tickets", { method: "POST", body: formData });

export const listTickets = () =>
  USE_MOCKS ? Promise.resolve(DEV_SAMPLE) : request("/api/tickets");

export const getTicket = (id) => request(`/api/tickets/${id}`);

export const updateStatus = (id, status) =>
  request(`/api/tickets/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
