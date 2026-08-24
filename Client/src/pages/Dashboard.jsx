import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import RiskCard from '../components/RiskCard';
import RiskMap from '../components/RiskMap';
import WeatherPanel from '../components/WeatherPanel';
import AlertPanel from '../components/AlertPanel';
import RoadStatus from '../components/RoadStatus';
import EmergencyPriority from '../components/EmergencyPriority';
import IncidentTable from '../components/IncidentTable';
import { KpiSkeleton, PanelSkeleton } from '../components/Skeleton';
import {
  getKpiSummary,
  getRiskZones,
  getIncidentMarkers,
  getInfrastructure,
  getAiPrediction,
  getWeather,
  getAlerts,
  getRoadSummary,
  getCriticalRoads,
  getEmergencyPriorities,
  getIncidentReports,
} from '../services/api';

const KPI_META = [
  { key: 'criticalZones', label: 'Critical Zones', icon: 'alert', band: 'CRITICAL' },
  { key: 'highRiskZones', label: 'High Risk Zones', icon: 'trend', band: 'HIGH' },
  { key: 'activeAlerts', label: 'Active Alerts', icon: 'bell', band: 'CRITICAL' },
  { key: 'roadsAffected', label: 'Roads Affected', icon: 'road', band: 'HIGH' },
];

export default function Dashboard({ selectedState }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);

  useEffect(() => {
    let alive = true;
    Promise.all([
      getKpiSummary(),
      getRiskZones(),
      getIncidentMarkers(),
      getInfrastructure(),
      getAiPrediction(),
      getWeather(),
      getAlerts(),
      getRoadSummary(),
      getCriticalRoads(),
      getEmergencyPriorities(),
      getIncidentReports(),
    ]).then(
      ([kpis, zones, incidents, infrastructure, prediction, weather, alerts, roadSummary, roads, priorities, reports]) => {
        if (!alive) return;
        setData({ kpis, zones, incidents, infrastructure, prediction, weather, alerts, roadSummary, roads, priorities, reports });
        setLoading(false);
      }
    );
    return () => {
      alive = false;
    };
  }, []);

  if (loading || !data) {
    return (
      <div className="page">
        <div className="kpi-grid">
          {KPI_META.map((k) => (
            <KpiSkeleton key={k.key} />
          ))}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <PanelSkeleton bodyHeight={700} />
        </div>
        <div className="grid-2">
          <PanelSkeleton bodyHeight={300} />
          <PanelSkeleton bodyHeight={300} />
        </div>
        <div className="grid-2">
          <PanelSkeleton bodyHeight={280} />
          <PanelSkeleton bodyHeight={280} />
        </div>
        <PanelSkeleton bodyHeight={260} />
      </div>
    );
  }

  return (
    <div className="page">
      {/* Risk Overview */}
      <div className="kpi-grid">
        {KPI_META.map((meta) => {
          const k = data.kpis[meta.key];
          return (
            <RiskCard
              key={meta.key}
              label={meta.label}
              icon={meta.icon}
              band={meta.band}
              value={k.value}
              note={k.note}
              delta={k.delta}
              trend={k.trend}
            />
          );
        })}
      </div>

      {/* Primary focal row: GIS Map */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <section className="panel map-panel panel--focus">
          <div className="panel-header">
            <div>
              <div className="panel-title">Live Landslide Risk Map</div>
              <div className="panel-subtitle">
                AI-generated risk assessment based on rainfall, soil moisture, terrain and historical landslide data.
              </div>
            </div>
            <span className="pill pill--neutral">
              <span className="live-dot" /> Live
            </span>
          </div>
          <RiskMap
            zones={data.zones}
            incidents={data.incidents}
            infrastructure={data.infrastructure}
            height={700}
            selectedState={selectedState}
          />
        </section>
      </div>

      {/* Warnings + Response priorities */}
      <div className="grid-2">
        <AlertPanel alerts={data.alerts} limit={3} onViewAll={() => navigate('/alerts')} onViewAlert={() => navigate('/alerts')} />
        <EmergencyPriority priorities={data.priorities} limit={3} onIssueWarning={() => navigate('/emergency')} />
      </div>

      {/* Weather + Road connectivity */}
      <div className="grid-2">
        <WeatherPanel weather={data.weather} />
        <RoadStatus summary={data.roadSummary} roads={data.roads} limit={4} onViewOnMap={() => navigate('/risk-map')} />
      </div>

      {/* Ground truth */}
      <IncidentTable reports={data.reports} />
    </div>
  );
}
