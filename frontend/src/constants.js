export const CATEGORY_LABELS = {
  plumbing: "Plumbing", electrical: "Electrical", hvac: "HVAC", structural: "Structural",
  furniture: "Furniture", cleanliness: "Cleanliness", it_network: "IT / Network",
  safety: "Safety", other: "Other",
};
export const PRIORITY_LABELS = { low: "Low", medium: "Medium", high: "High", urgent: "Urgent" };
export const STATUS_LABELS = { open: "Open", in_progress: "In Progress", resolved: "Resolved", closed: "Closed" };
export const VERIFICATION_LABELS = {
  consistent: "Evidence consistent",
  needs_review: "Needs human review",
  insufficient: "Not enough detail",
  not_assessed: "Not assessed",
};

export const label = (map, key) => map[key] || key || "Unknown";

export const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
export const IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];
