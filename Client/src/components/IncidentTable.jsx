import { useMemo, useState } from 'react';
import Icon from './Icon';
import StatusPill from './StatusPill';

const FILTERS = ['All', 'Critical', 'High', 'Pending', 'Verified'];

// Recent incident reports table with severity/status filtering.
export default function IncidentTable({ reports = [], title = 'Recent Incident Reports' }) {
  const [filter, setFilter] = useState('All');

  const rows = useMemo(() => {
    if (filter === 'All') return reports;
    if (filter === 'Critical') return reports.filter((r) => r.severity === 'CRITICAL');
    if (filter === 'High') return reports.filter((r) => r.severity === 'HIGH');
    return reports.filter((r) => r.status === filter);
  }, [reports, filter]);

  return (
    <section className="panel">
      <div className="panel-header" style={{ flexWrap: 'wrap' }}>
        <div>
          <div className="panel-title">{title}</div>
          <div className="panel-subtitle">Geo-tagged ground truth from citizens and field officers</div>
        </div>
        <div className="table-filters">
          {FILTERS.map((f) => (
            <button
              key={f}
              className={`filter-chip ${filter === f ? 'active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th>Location</th>
              <th>Incident</th>
              <th>Severity</th>
              <th>Source</th>
              <th>Time</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td className="cell-strong">
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <Icon name="location" size={13} style={{ color: 'var(--color-ink-muted)' }} />
                    {r.location}
                  </span>
                </td>
                <td>{r.incident}</td>
                <td>
                  <StatusPill status={r.severity} />
                </td>
                <td>{r.source}</td>
                <td className="mono">{r.time}</td>
                <td>
                  <span className={`status-tag ${r.status === 'Verified' ? 'verified' : 'pending'}`}>
                    <Icon name={r.status === 'Verified' ? 'checkCircle' : 'clock'} size={13} />
                    {r.status}
                  </span>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={6}>
                  <div className="empty">No reports match this filter.</div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
