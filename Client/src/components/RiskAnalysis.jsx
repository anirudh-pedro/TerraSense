import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import Icon from './Icon';
import { bandForScore } from '../data/mockData';

// SVG circular gauge (0-100). Arc color follows the risk band.
function Gauge({ score }) {
  const band = bandForScore(score);
  const size = 168;
  const stroke = 12;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (score / 100) * c;
  return (
    <div className="gauge">
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--color-surface-2)" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={band.color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
      </svg>
      <div className="gauge-center">
        <span className="gauge-score" style={{ color: band.color }}>
          {score}%
        </span>
        <span className="gauge-label" style={{ color: band.color }}>
          {band.label.toUpperCase()} RISK
        </span>
      </div>
    </div>
  );
}

function factorColor(weight) {
  return bandForScore(weight * 100).color;
}

function TrendTooltip({ active, payload, label }) {
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
      <div style={{ fontWeight: 700, color: bandForScore(payload[0].value).color }}>
        Risk {payload[0].value}%
      </div>
    </div>
  );
}

export default function RiskAnalysis({ prediction, className = '' }) {
  if (!prediction) return null;
  const band = bandForScore(prediction.riskScore);

  return (
    <section className={`panel ${className}`.trim()}>
      <div className="panel-header">
        <div>
          <div className="panel-title">AI Risk Prediction</div>
          <div className="panel-subtitle">
            {prediction.district}, {prediction.state}
          </div>
        </div>
        <span className="eyebrow">Model v3.2</span>
      </div>

      <div className="panel-body">
        <div className="gauge-wrap">
          <Gauge score={prediction.riskScore} />
          <p className="ai-summary">{prediction.summary}</p>
          <span className="ai-window-tag">
            <Icon name="clock" size={13} />
            {prediction.predictionWindow}
          </span>
        </div>

        <div className="subhead" style={{ marginTop: 18 }}>Risk Factors</div>
        <div className="factor-list">
          {prediction.factors.map((f) => (
            <div className="factor" key={f.name}>
              <div className="factor-top">
                <span className="factor-name">{f.name}</span>
                <span className="factor-level" style={{ color: factorColor(f.weight) }}>
                  {f.level}
                </span>
              </div>
              <div className="factor-bar">
                <div
                  className="factor-fill"
                  style={{ width: `${f.weight * 100}%`, background: factorColor(f.weight) }}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="subhead" style={{ marginTop: 22 }}>24-Hour Risk Trend</div>
        <div className="chart-box" style={{ height: 168 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={prediction.trend} margin={{ top: 6, right: 8, left: -16, bottom: 0 }}>
              <defs>
                <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={band.color} stopOpacity={0.45} />
                  <stop offset="100%" stopColor={band.color} stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="var(--color-line)" strokeDasharray="2 4" vertical={false} />
              <XAxis
                dataKey="time"
                tick={{ fill: 'var(--color-ink-2)', fontSize: 11 }}
                interval={2}
                tickLine={false}
                axisLine={{ stroke: 'var(--color-line)' }}
                dy={4}
              />
              <YAxis
                domain={[0, 100]}
                ticks={[0, 25, 50, 75, 100]}
                tick={{ fill: 'var(--color-ink-2)', fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                width={38}
              />
              <ReferenceLine
                y={70}
                stroke="var(--color-risk-critical)"
                strokeDasharray="4 4"
                strokeOpacity={0.7}
                label={{ value: 'Critical', position: 'insideTopRight', fill: 'var(--color-risk-critical)', fontSize: 10 }}
              />
              <Tooltip content={<TrendTooltip />} cursor={{ stroke: 'var(--color-line-strong)', strokeWidth: 1 }} />
              <Area
                type="monotone"
                dataKey="risk"
                stroke={band.color}
                strokeWidth={2.4}
                fill="url(#riskGrad)"
                dot={false}
                activeDot={{ r: 4, fill: band.color, stroke: '#0b1220', strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}
