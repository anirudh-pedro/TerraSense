import Icon from './Icon';
import StatusPill from './StatusPill';

// Compact road connectivity module: summary counts + critical road list.
export default function RoadStatus({ summary, roads = [], limit, onViewOnMap }) {
  const list = limit ? roads.slice(0, limit) : roads;

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">Road Connectivity</div>
          <div className="panel-subtitle">{summary?.atRisk ?? roads.length} roads at risk</div>
        </div>
        <Icon name="road" size={18} style={{ color: 'var(--color-ink-2)' }} />
      </div>

      <div className="panel-body">
        <div className="road-summary">
          <div className="road-stat open">
            <div className="rs-value">{summary?.open ?? 0}</div>
            <div className="rs-label">Open</div>
          </div>
          <div className="road-stat restricted">
            <div className="rs-value">{summary?.restricted ?? 0}</div>
            <div className="rs-label">Restricted</div>
          </div>
          <div className="road-stat blocked">
            <div className="rs-value">{summary?.blocked ?? 0}</div>
            <div className="rs-label">Blocked</div>
          </div>
        </div>

        {list.map((r) => (
          <div className="road-item" key={r.id}>
            <Icon name="road" size={17} className="road-ico" />
            <div className="road-info">
              <div className="road-name">{r.name}</div>
              <div className="road-note">{r.note}</div>
            </div>
            <StatusPill status={r.status} band={r.band} label={r.status} />
            <button className="link-btn" onClick={() => onViewOnMap?.(r)}>
              View on Map
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
