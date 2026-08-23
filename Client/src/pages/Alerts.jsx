import AlertPanel from '../components/AlertPanel';
import WeatherPanel from '../components/WeatherPanel';
import { ALERTS, WEATHER } from '../data/mockData';

export default function Alerts() {
  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Active Early Warnings</h1>
          <p>AI-issued landslide warnings across NER districts, ranked by probability and severity.</p>
        </div>
        <div className="page-head-actions">
          <span className="pill pill--critical">
            <span className="dot" />
            {ALERTS.filter((a) => a.status === 'CRITICAL').length} Critical
          </span>
          <span className="pill pill--high">
            <span className="dot" />
            {ALERTS.filter((a) => a.status === 'HIGH').length} High
          </span>
        </div>
      </div>

      <div className="grid-2">
        <AlertPanel alerts={ALERTS} showViewAll={false} />
        <div className="dash-col">
          <WeatherPanel weather={WEATHER} />
        </div>
      </div>
    </div>
  );
}
