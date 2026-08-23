import RiskCard from '../components/RiskCard';
import Icon from '../components/Icon';
import { SYSTEM_STATUS } from '../data/mockData';

export default function SystemStatus() {
  const s = SYSTEM_STATUS;
  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>System Status</h1>
          <p>Health of the TerraSense sensing network, data feeds and prediction model.</p>
        </div>
        <span className="pill pill--low">
          <span className="dot" /> {s.overall}
        </span>
      </div>

      <div className="kpi-grid">
        <RiskCard label="Sensors Online" value={`${s.sensors.online}/${s.sensors.total}`} note="Ground + telemetry" icon="activity" band="LOW" />
        <RiskCard label="AI Model" value={s.aiModel} note="Nowcast engine" icon="trend" band="LOW" />
        <RiskCard label="Data Feeds" value={`${s.dataFeeds.filter((f) => f.status === 'Live').length}/${s.dataFeeds.length}`} note="Live ingestion" icon="layers" band="MODERATE" />
        <RiskCard label="Network Mode" value="Low-BW" note={s.network} icon="globe" band="MODERATE" />
      </div>

      <div className="grid-2">
        <section className="panel">
          <div className="panel-header">
            <div className="panel-title">Data Feeds</div>
          </div>
          <div className="panel-body">
            {s.dataFeeds.map((f) => (
              <div className="status-feed" key={f.name}>
                <span className="cell-strong" style={{ color: 'var(--color-ink)' }}>{f.name}</span>
                <span className={`status-tag ${f.status === 'Live' ? 'verified' : 'pending'}`}>
                  <Icon name={f.status === 'Live' ? 'checkCircle' : 'clock'} size={14} />
                  {f.status}
                </span>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div className="panel-title">Resilience</div>
            <div className="panel-subtitle">Designed for fragile, low-network hill terrain</div>
          </div>
          <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="priority-action">
              <Icon name="globe" size={15} style={{ color: 'var(--color-accent)', flex: 'none', marginTop: 1 }} />
              <span><b>Low-bandwidth mode</b> caches critical alerts and map tiles for offline-first delivery.</span>
            </div>
            <div className="priority-action">
              <Icon name="bell" size={15} style={{ color: 'var(--color-accent)', flex: 'none', marginTop: 1 }} />
              <span><b>Multilingual alerts</b> dispatched via SMS and push in regional languages.</span>
            </div>
            <div className="priority-action">
              <Icon name="activity" size={15} style={{ color: 'var(--color-accent)', flex: 'none', marginTop: 1 }} />
              <span><b>Edge sensing</b> continues local risk scoring during connectivity loss.</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
