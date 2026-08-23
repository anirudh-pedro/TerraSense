import { useEffect, useState } from 'react';
import Icon from './Icon';
import { INCIDENT_TYPES } from '../data/mockData';
import { submitIncidentReport } from '../services/api';

// Fallback coordinate (Aizawl) used when geolocation is unavailable/denied —
// keeps the demo functional in low-network / permission-blocked environments.
const FALLBACK_COORDS = { lat: 23.7271, lng: 92.7176 };

export default function IncidentModal({ open, onClose, onSubmitted }) {
  const [type, setType] = useState(INCIDENT_TYPES[0]);
  const [coords, setCoords] = useState(FALLBACK_COORDS);
  // Lazy init avoids a synchronous setState inside the effect below.
  const [locating, setLocating] = useState(() => typeof navigator !== 'undefined' && !!navigator.geolocation);
  const [photo, setPhoto] = useState(null);
  const [video, setVideo] = useState(null);
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  // Capture GPS position when the modal opens. State is only updated from the
  // async geolocation callbacks (never synchronously in the effect body).
  useEffect(() => {
    if (!open || typeof navigator === 'undefined' || !navigator.geolocation) return;
    let cancelled = false;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        if (cancelled) return;
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLocating(false);
      },
      () => !cancelled && setLocating(false),
      { enableHighAccuracy: true, timeout: 8000 }
    );
    return () => {
      cancelled = true;
    };
  }, [open]);

  if (!open) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    const payload = {
      incident: type,
      severity: 'HIGH',
      source: 'Citizen',
      location: `${coords.lat.toFixed(4)}, ${coords.lng.toFixed(4)}`,
      coords,
      description,
      photo: photo?.name ?? null,
      video: video?.name ?? null,
    };
    const record = await submitIncidentReport(payload);
    setSubmitting(false);
    setResult(record);
    onSubmitted?.(record);
  }

  function reset() {
    setType(INCIDENT_TYPES[0]);
    setPhoto(null);
    setVideo(null);
    setDescription('');
    setResult(null);
  }

  return (
    <div className="modal-overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal fade-up" role="dialog" aria-modal="true">
        <div className="modal-head">
          <div>
            <h3>Report Incident</h3>
            <p>For citizens and field officials · geo-tagged ground truth</p>
          </div>
          <button className="icon-btn" onClick={onClose} aria-label="Close">
            <Icon name="close" size={18} />
          </button>
        </div>

        {result ? (
          <div className="modal-body">
            <div className="submit-success">
              <div className="success-check">
                <Icon name="check" size={30} strokeWidth={2.5} />
              </div>
              <h3>Report received successfully</h3>
              <p>Your report has been logged and routed for verification.</p>

              <div className="success-detail">
                <div className="sd-row">
                  <span>Reference</span>
                  <b className="mono">{result.id}</b>
                </div>
                <div className="sd-row">
                  <span>Incident</span>
                  <b>{result.incident}</b>
                </div>
                <div className="sd-row">
                  <span>Location</span>
                  <b className="mono">{result.location}</b>
                </div>
                <div className="sd-row">
                  <span>Status</span>
                  <b style={{ color: 'var(--color-risk-moderate)' }}>{result.status}</b>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="modal-body">
              <div className="field">
                <label className="field-label">Incident Type</label>
                <select className="select" value={type} onChange={(e) => setType(e.target.value)}>
                  {INCIDENT_TYPES.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label className="field-label">Location</label>
                <div className="gps-box">
                  <Icon name="location" size={20} className="gps-ico" />
                  <div className="gps-coords">
                    <div className="g-label">Latitude / Longitude {locating && '· locating…'}</div>
                    {coords.lat.toFixed(5)}, {coords.lng.toFixed(5)}
                  </div>
                </div>
              </div>

              <div className="field">
                <label className="field-label">Media</label>
                <div className="upload-row">
                  <label className={`upload-box ${photo ? 'filled' : ''}`}>
                    <Icon name="camera" size={20} />
                    {photo ? photo.name.slice(0, 18) : 'Upload Photo'}
                    <input
                      type="file"
                      accept="image/*"
                      hidden
                      onChange={(e) => setPhoto(e.target.files?.[0] ?? null)}
                    />
                  </label>
                  <label className={`upload-box ${video ? 'filled' : ''}`}>
                    <Icon name="video" size={20} />
                    {video ? video.name.slice(0, 18) : 'Upload Video (optional)'}
                    <input
                      type="file"
                      accept="video/*"
                      hidden
                      onChange={(e) => setVideo(e.target.files?.[0] ?? null)}
                    />
                  </label>
                </div>
              </div>

              <div className="field" style={{ marginBottom: 0 }}>
                <label className="field-label">Description</label>
                <textarea
                  className="textarea"
                  placeholder="Describe the incident — what you observed, when, and any immediate risk to people or roads."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
            </div>

            <div className="modal-foot">
              <button type="button" className="btn btn--ghost" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="btn btn--primary" disabled={submitting}>
                {submitting ? 'Submitting…' : 'Submit Report'}
              </button>
            </div>
          </form>
        )}

        {result && (
          <div className="modal-foot">
            <button className="btn btn--ghost" onClick={reset}>
              Report Another
            </button>
            <button className="btn btn--primary" onClick={onClose}>
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
