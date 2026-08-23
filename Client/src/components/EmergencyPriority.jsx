import Icon from './Icon';
import StatusPill from './StatusPill';
import { bandForScore } from '../data/mockData';

// Ranked emergency response priorities — the "what should authorities do" module.
export default function EmergencyPriority({ priorities = [], limit, onIssueWarning }) {
  const list = limit ? priorities.slice(0, limit) : priorities;

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">Emergency Response Priorities</div>
          <div className="panel-subtitle">Ranked by risk, population exposure and access</div>
        </div>
        <Icon name="shield" size={18} style={{ color: 'var(--color-ink-2)' }} />
      </div>

      <div className="panel-body">
        {list.map((p) => {
          const rankClass = p.status === 'CRITICAL' ? 'critical' : 'high';
          return (
            <div className="priority-item" key={p.id}>
              <div className={`priority-rank ${rankClass}`}>
                <span className="pr-hash">#</span>
                <span className="pr-num">{p.rank}</span>
              </div>

              <div className="priority-body">
                <div className="priority-head">
                  <span className="priority-district">{p.district}</span>
                  <StatusPill status={p.status} />
                </div>

                <div className="priority-meta">
                  <div className="pm">
                    <span className="pm-label">Risk</span>
                    <span className="pm-value" style={{ color: bandForScore(p.risk).color }}>
                      {p.risk}%
                    </span>
                  </div>
                  <div className="pm">
                    <span className="pm-label">Population Exposed</span>
                    <span className="pm-value">{p.populationExposed.toLocaleString()}</span>
                  </div>
                  <div className="pm">
                    <span className="pm-label">Road Status</span>
                    <span className="pm-value" style={{ fontSize: 13 }}>{p.roadStatus}</span>
                  </div>
                </div>

                <div className="priority-action">
                  <Icon name="checkCircle" size={15} style={{ color: 'var(--color-accent)', flex: 'none', marginTop: 1 }} />
                  <span>
                    <b>Recommended:</b> {p.action}
                  </span>
                </div>

                {onIssueWarning && (
                  <button
                    className="btn btn--sm btn--danger"
                    style={{ marginTop: 10 }}
                    onClick={() => onIssueWarning(p)}
                  >
                    <Icon name="alert" size={14} />
                    Issue Warning
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
