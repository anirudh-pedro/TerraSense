import Icon from './Icon';
import StatusPill from './StatusPill';

const bandClass = { CRITICAL: 'critical', HIGH: 'high', MODERATE: 'moderate' };

// Active early-warning list. `limit` trims for the compact dashboard card.
export default function AlertPanel({ alerts = [], limit, onViewAlert, onViewAll, showViewAll = true }) {
  const list = limit ? alerts.slice(0, limit) : alerts;

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">Active Early Warnings</div>
          <div className="panel-subtitle">{alerts.length} warnings currently issued</div>
        </div>
        <span className="pill pill--critical">
          <span className="dot" />
          {alerts.filter((a) => a.status === 'CRITICAL').length} Critical
        </span>
      </div>

      <div className="panel-body">
        <div className="alert-list">
          {list.map((a) => (
            <article className={`alert-item ${bandClass[a.status] || 'high'}`} key={a.id}>
              <div className="alert-top">
                <span className="alert-district">{a.district}</span>
                <StatusPill status={a.status} />
              </div>

              <div className="alert-prob">
                <b>{a.probability}%</b>
                <span>Landslide Probability</span>
              </div>

              <p className="alert-msg">{a.message}</p>

              <div className="alert-foot">
                <span className="alert-issued">
                  <Icon name="clock" size={12} />
                  Issued {a.issued}
                </span>
                <button className="btn btn--sm btn--ghost" onClick={() => onViewAlert?.(a)}>
                  View Alert
                </button>
              </div>
            </article>
          ))}
        </div>

        {showViewAll && (
          <button className="btn btn--ghost btn--block" style={{ marginTop: 14 }} onClick={onViewAll}>
            View All Alerts
            <Icon name="chevronRight" size={15} />
          </button>
        )}
      </div>
    </section>
  );
}
