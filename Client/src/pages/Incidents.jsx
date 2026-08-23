import IncidentTable from '../components/IncidentTable';
import RiskCard from '../components/RiskCard';
import Icon from '../components/Icon';
import { INCIDENT_REPORTS } from '../data/mockData';

export default function Incidents({ onReportIncident }) {
  const total = INCIDENT_REPORTS.length;
  const pending = INCIDENT_REPORTS.filter((r) => r.status === 'Pending').length;
  const verified = INCIDENT_REPORTS.filter((r) => r.status === 'Verified').length;
  const critical = INCIDENT_REPORTS.filter((r) => r.severity === 'CRITICAL').length;

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Incident Reports</h1>
          <p>Geo-tagged ground truth submitted by citizens and field officials, verified against AI risk models.</p>
        </div>
        <div className="page-head-actions">
          <button className="btn btn--danger" onClick={onReportIncident}>
            <Icon name="plus" size={16} />
            Report Incident
          </button>
        </div>
      </div>

      <div className="kpi-grid">
        <RiskCard label="Total Reports" value={total} note="Last 24 hours" icon="clipboard" band="MODERATE" />
        <RiskCard label="Critical" value={critical} note="Require immediate review" icon="alert" band="CRITICAL" />
        <RiskCard label="Pending Verification" value={pending} note="Awaiting field confirmation" icon="clock" band="HIGH" />
        <RiskCard label="Verified" value={verified} note="Confirmed by officers" icon="checkCircle" band="LOW" />
      </div>

      <IncidentTable reports={INCIDENT_REPORTS} title="All Incident Reports" />
    </div>
  );
}
