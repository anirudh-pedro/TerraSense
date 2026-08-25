import RiskMap from '../components/RiskMap';
import RiskAnalysis from '../components/RiskAnalysis';
import WeatherPanel from '../components/WeatherPanel';
import {
  RISK_ZONES,
  INCIDENT_MARKERS,
  INFRASTRUCTURE,
  AI_PREDICTION,
} from '../data/mockData';

export default function RiskMapPage() {
  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Live Risk Map</h1>
          <p>Full-screen GIS view of AI-assessed landslide risk zones, incidents and critical infrastructure across the NER.</p>
        </div>
      </div>

      <div className="dash-grid">
        <section className="panel map-panel panel--focus">
          <div className="panel-header">
            <div>
              <div className="panel-title">Live Landslide Risk Map</div>
              <div className="panel-subtitle">
                Click any risk zone to inspect its environmental profile and prediction window.
              </div>
            </div>
            <span className="pill pill--neutral">
              <span className="live-dot" /> Live
            </span>
          </div>
          <RiskMap
            fill
            zones={RISK_ZONES}
            incidents={INCIDENT_MARKERS}
            infrastructure={INFRASTRUCTURE}
          />
        </section>

        <div className="dash-col">
          <RiskAnalysis className="panel--focus" prediction={AI_PREDICTION} />
          <WeatherPanel district="Aizawl" />
        </div>
      </div>
    </div>
  );
}
