import EmergencyPriority from '../components/EmergencyPriority';
import RoadStatus from '../components/RoadStatus';
import RiskCard from '../components/RiskCard';
import {
  EMERGENCY_PRIORITIES,
  ROAD_SUMMARY,
  CRITICAL_ROADS,
} from '../data/mockData';

export default function EmergencyResponse() {
  const totalExposed = EMERGENCY_PRIORITIES.reduce((sum, p) => sum + p.populationExposed, 0);
  const criticalCount = EMERGENCY_PRIORITIES.filter((p) => p.status === 'CRITICAL').length;

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Emergency Response</h1>
          <p>Prioritised response plan combining AI risk, population exposure and road access to direct teams where they matter most.</p>
        </div>
      </div>

      <div className="kpi-grid">
        <RiskCard label="Priority Districts" value={EMERGENCY_PRIORITIES.length} note="Under active coordination" icon="shield" band="HIGH" />
        <RiskCard label="Critical Priority" value={criticalCount} note="Deploy teams now" icon="alert" band="CRITICAL" />
        <RiskCard label="Population Exposed" value={totalExposed.toLocaleString()} note="Across priority zones" icon="users" band="HIGH" />
        <RiskCard label="Roads Blocked" value={ROAD_SUMMARY.blocked} note="Impeding access" icon="road" band="CRITICAL" />
      </div>

      <div className="grid-2">
        <EmergencyPriority priorities={EMERGENCY_PRIORITIES} onIssueWarning={() => {}} />
        <div className="dash-col">
          <RoadStatus summary={ROAD_SUMMARY} roads={CRITICAL_ROADS} />
        </div>
      </div>
    </div>
  );
}
