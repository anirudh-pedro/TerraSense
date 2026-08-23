import Icon from './Icon';
import { RISK_BANDS } from '../data/mockData';

// Tiny inline sparkline (no chart lib needed for a KPI micro-viz).
function Sparkline({ data = [], color, width = 72, height = 26 }) {
  if (data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const span = max - min || 1;
  const step = width / (data.length - 1);
  const pts = data.map((v, i) => [i * step, height - ((v - min) / span) * (height - 4) - 2]);
  const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');
  const area = `${line} L${width},${height} L0,${height} Z`;
  const gid = `spark-${color.replace('#', '')}`;
  return (
    <svg className="kpi-spark" width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.35" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gid})`} />
      <path d={line} fill="none" stroke={color} strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

const DELTA_ICON = { up: 'trend', down: 'trend', flat: 'activity' };

// Compact KPI card. `band` drives the accent color (status only).
export default function RiskCard({ label, value, note, icon, band = 'HIGH', delta, trend }) {
  const b = RISK_BANDS[band] ?? RISK_BANDS.HIGH;
  return (
    <div
      className="risk-card fade-up"
      style={{ '--band-color': b.color, '--band-soft': `${b.color}22` }}
    >
      <div className="risk-card-top">
        <span className="risk-card-label">{label}</span>
        <span className="risk-card-ico">
          <Icon name={icon} size={19} />
        </span>
      </div>

      <div className="risk-card-value">{value}</div>

      <div className="risk-card-foot">
        {delta && (
          <span className={`kpi-delta ${delta.dir}`}>
            <Icon
              name={DELTA_ICON[delta.dir]}
              size={12}
              style={{ transform: delta.dir === 'down' ? 'scaleY(-1)' : 'none' }}
            />
            {delta.text}
          </span>
        )}
        {trend && <Sparkline data={trend} color={b.color} />}
      </div>

      <div className="risk-card-note">{note}</div>
    </div>
  );
}
