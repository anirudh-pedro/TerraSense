import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from 'recharts';
import Icon from './Icon';

const STAT_ICONS = {
  Temperature: 'thermometer',
  Humidity: 'droplet',
  Rainfall: 'cloudRain',
  Wind: 'wind',
};

// Rainfall intensity color: heavier rain trends toward the high/critical palette.
function rainColor(mm) {
  if (mm >= 50) return 'var(--color-risk-critical)';
  if (mm >= 40) return 'var(--color-risk-high)';
  if (mm >= 25) return 'var(--color-risk-moderate)';
  return 'var(--color-accent)';
}

function RainTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: '#111927',
        border: '1px solid var(--color-line-strong)',
        borderRadius: 8,
        padding: '8px 11px',
        fontSize: 12,
        boxShadow: '0 6px 16px rgba(2, 6, 14, 0.35)',
      }}
    >
      <div style={{ color: 'var(--color-ink-muted)', marginBottom: 2 }}>{label}</div>
      <div style={{ fontWeight: 700 }}>{payload[0].value} mm/hr</div>
    </div>
  );
}

export default function WeatherPanel({ weather }) {
  if (!weather) return null;
  const stats = [
    { label: 'Temperature', value: `${weather.temperature}°C` },
    { label: 'Humidity', value: `${weather.humidity}%` },
    { label: 'Rainfall', value: `${weather.rainfall} mm/hr` },
    { label: 'Wind', value: `${weather.wind} km/h` },
  ];

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">Weather &amp; Rainfall Risk</div>
          <div className="panel-subtitle">{weather.district} · live conditions</div>
        </div>
        <Icon name="cloudRain" size={18} style={{ color: 'var(--color-ink-2)' }} />
      </div>

      <div className="panel-body">
        <div className="weather-grid">
          {stats.map((s) => (
            <div className="weather-stat" key={s.label}>
              <span className="ws-ico">
                <Icon name={STAT_ICONS[s.label]} size={17} />
              </span>
              <span className="ws-text">
                <span className="ws-label">{s.label}</span>
                <span className="ws-value">{s.value}</span>
              </span>
            </div>
          ))}
        </div>

        <div className="subhead" style={{ marginTop: 18 }}>12-Hour Rainfall Forecast</div>
        <div className="chart-box" style={{ height: 156 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={weather.forecast} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
              <CartesianGrid stroke="var(--color-line)" strokeDasharray="2 4" vertical={false} />
              <XAxis
                dataKey="time"
                tick={{ fill: 'var(--color-ink-2)', fontSize: 11 }}
                interval={1}
                tickLine={false}
                axisLine={{ stroke: 'var(--color-line)' }}
                dy={4}
              />
              <YAxis
                tick={{ fill: 'var(--color-ink-2)', fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                width={38}
                unit=""
              />
              <Tooltip content={<RainTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
              <Bar dataKey="rain" radius={[4, 4, 0, 0]} maxBarSize={26}>
                {weather.forecast.map((d, i) => (
                  <Cell key={i} fill={rainColor(d.rain)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {weather.warning && (
          <div className="warn-banner">
            <Icon name="alert" size={16} className="wb-ico" />
            {weather.warning}
          </div>
        )}
      </div>
    </section>
  );
}
