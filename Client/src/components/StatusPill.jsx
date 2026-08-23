// Renders a risk/status pill using the shared band styling.
// `status` accepts a band key (LOW | MODERATE | HIGH | CRITICAL) or free text
// like "BLOCKED" / "RESTRICTED" that maps to a band.

const STATUS_TO_BAND = {
  LOW: 'low',
  MODERATE: 'moderate',
  RESTRICTED: 'moderate',
  HIGH: 'high',
  'HIGH RISK': 'high',
  CRITICAL: 'critical',
  BLOCKED: 'critical',
};

export default function StatusPill({ status, label, band }) {
  const key = (band || STATUS_TO_BAND[String(status).toUpperCase()] || 'neutral').toLowerCase();
  return (
    <span className={`pill pill--${key}`}>
      <span className="dot" />
      {label ?? status}
    </span>
  );
}
