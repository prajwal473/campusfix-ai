import { useEffect, useState } from "react";
import { createTicket } from "../api.js";
import { IMAGE_TYPES, MAX_IMAGE_BYTES } from "../constants.js";

export default function ReportForm({ onCreated }) {
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => () => preview && URL.revokeObjectURL(preview), [preview]);

  function pickImage(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!IMAGE_TYPES.includes(file.type)) {
      setErrors((p) => ({ ...p, image: "Use a JPEG, PNG or WebP image." }));
      e.target.value = "";
      return;
    }
    if (file.size > MAX_IMAGE_BYTES) {
      setErrors((p) => ({ ...p, image: "Image is too large. Maximum size is 5 MB." }));
      e.target.value = "";
      return;
    }
    setErrors((p) => ({ ...p, image: "" }));
    setImage(file);
    setPreview(URL.createObjectURL(file));
  }

  function removeImage() {
    setImage(null);
    setPreview(null);
    setErrors((p) => ({ ...p, image: "" }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const next = {};
    if (!description.trim()) next.description = "Describe the problem so staff know what to look for.";
    if (!location.trim()) next.location = "Add the building, floor or room.";
    setErrors(next);
    setSubmitError("");
    if (Object.keys(next).length) return;

    const body = new FormData();
    body.append("description", description.trim());
    body.append("location", location.trim());
    if (image) body.append("image", image);

    setLoading(true);
    try {
      const ticket = await createTicket(body);
      onCreated(ticket);
    } catch (err) {
      setSubmitError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="panel form" onSubmit={handleSubmit} noValidate>
      <h2>Report a problem</h2>

      <label htmlFor="description">What is wrong?</label>
      <textarea
        id="description" rows={4} value={description} disabled={loading}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Example: Water is dripping from the ceiling and the floor is wet."
        aria-invalid={!!errors.description}
      />
      {errors.description && <p className="field-error" role="alert">{errors.description}</p>}

      <label htmlFor="location">Where is it?</label>
      <input
        id="location" type="text" value={location} disabled={loading}
        onChange={(e) => setLocation(e.target.value)}
        placeholder="Building, floor, room"
        aria-invalid={!!errors.location}
      />
      {errors.location && <p className="field-error" role="alert">{errors.location}</p>}

      <label htmlFor="image">Photo (optional)</label>
      {!preview && (
        <input id="image" type="file" accept="image/jpeg,image/png,image/webp" onChange={pickImage} disabled={loading} />
      )}
      {preview && (
        <div className="preview">
          <img src={preview} alt="Selected upload preview" />
          <button type="button" className="btn-secondary" onClick={removeImage} disabled={loading}>
            Remove photo
          </button>
        </div>
      )}
      {errors.image && <p className="field-error" role="alert">{errors.image}</p>}

      {submitError && <p className="banner banner-error" role="alert">{submitError}</p>}

      <button type="submit" className="btn-primary" disabled={loading}>
        {loading ? "Analysing…" : "Submit report"}
      </button>
    </form>
  );
}
