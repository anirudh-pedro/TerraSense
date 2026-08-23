import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Circle, CircleMarker, Tooltip, LayersControl, useMap } from 'react-leaflet';
import Icon from './Icon';
import StatusPill from './StatusPill';
import { RISK_BANDS, bandForScore, REGION_META } from '../data/mockData';

const LEGEND = [
  { band: RISK_BANDS.LOW, label: 'Low', range: '0–20%' },
  { band: RISK_BANDS.MODERATE, label: 'Moderate', range: '20–40%' },
  { band: RISK_BANDS.HIGH, label: 'High', range: '40–70%' },
  { band: RISK_BANDS.CRITICAL, label: 'Critical', range: '70–100%' },
];

// Keeps Leaflet correctly sized when the container is a flex child that
// resolves its height after layout (fill mode) or when the viewport resizes.
function MapResizer() {
  const map = useMap();
  useEffect(() => {
    const invalidate = () => map.invalidateSize();
    const t = setTimeout(invalidate, 180);
    const ro = new ResizeObserver(invalidate);
    ro.observe(map.getContainer());
    return () => {
      clearTimeout(t);
      ro.disconnect();
    };
  }, [map]);
  return null;
}

// Fill opacity scales with severity so critical zones read strongest.
function zoneStyle(score) {
  const color = bandForScore(score).color;
  const opacity = 0.18 + (score / 100) * 0.32;
  return { color, fillColor: color, fillOpacity: opacity, weight: 1.5 };
}

export default function RiskMap({
  zones = [],
  incidents = [],
  infrastructure = [],
  onViewAnalysis,
  center = REGION_META.center,
  zoom = REGION_META.zoom,
  height = 560,
  fill = false,
}) {
  const [selected, setSelected] = useState(null);
  const [show, setShow] = useState({ zones: true, incidents: true, infra: true });

  const toggle = (key) => setShow((s) => ({ ...s, [key]: !s[key] }));

  return (
    <div className={fill ? 'map-wrap map-wrap--fill' : 'map-wrap'} style={fill ? undefined : { height }}>
      <MapContainer
        center={center}
        zoom={zoom}
        className="risk-map"
        scrollWheelZoom
        zoomControl
      >
        <MapResizer />
        <LayersControl position="topleft">
          <LayersControl.BaseLayer checked name="Dark (OSM)">
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="Street (OSM)">
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="Terrain">
            <TileLayer
              url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
              attribution='&copy; OpenStreetMap contributors, SRTM | &copy; OpenTopoMap'
            />
          </LayersControl.BaseLayer>
        </LayersControl>

        {/* Risk zones */}
        {show.zones &&
          zones.map((z) => (
            <Circle
              key={z.id}
              center={z.center}
              radius={z.radius}
              pathOptions={zoneStyle(z.riskScore)}
              eventHandlers={{ click: () => setSelected(z) }}
            >
              <Tooltip direction="top" opacity={1}>
                <b>{z.district}</b> — {z.riskScore}% ({z.status})
              </Tooltip>
            </Circle>
          ))}

        {/* Incident markers */}
        {show.incidents &&
          incidents.map((i) => {
            const color = bandForScore(i.severity === 'CRITICAL' ? 90 : i.severity === 'HIGH' ? 55 : 30).color;
            return (
              <CircleMarker
                key={i.id}
                center={i.coords}
                radius={6}
                pathOptions={{ color: '#0b1220', weight: 2, fillColor: color, fillOpacity: 1 }}
              >
                <Tooltip direction="top">
                  {i.type} · {i.location}
                </Tooltip>
              </CircleMarker>
            );
          })}

        {/* Critical infrastructure */}
        {show.infra &&
          infrastructure.map((f) => (
            <CircleMarker
              key={f.id}
              center={f.coords}
              radius={5}
              pathOptions={{ color: '#cfe0ff', weight: 2, fillColor: '#3b82f6', fillOpacity: 0.9 }}
            >
              <Tooltip direction="top">
                {f.name} · {f.type}
              </Tooltip>
            </CircleMarker>
          ))}
      </MapContainer>

      {/* Layer toggles */}
      <div className="map-controls">
        <button className={`map-toggle ${show.zones ? 'on' : ''}`} onClick={() => toggle('zones')}>
          <Icon name="layers" size={13} /> Risk Zones
        </button>
        <button className={`map-toggle ${show.incidents ? 'on' : ''}`} onClick={() => toggle('incidents')}>
          <Icon name="location" size={13} /> Incidents
        </button>
        <button className={`map-toggle ${show.infra ? 'on' : ''}`} onClick={() => toggle('infra')}>
          <Icon name="shield" size={13} /> Infrastructure
        </button>
      </div>

      {/* Legend */}
      <div className="map-legend">
        <div className="lg-title">Landslide Risk</div>
        {LEGEND.map((l) => (
          <div className="lg-row" key={l.label}>
            <span className="lg-swatch" style={{ background: l.band.color }} />
            {l.label} <span style={{ color: 'var(--color-ink-muted)' }}>{l.range}</span>
          </div>
        ))}
      </div>

      {/* Zone info panel */}
      {selected && (
        <div className="zone-panel fade-up">
          <div className="zone-panel-head">
            <div>
              <h4>{selected.district} District</h4>
              <span className="z-state">{selected.state}</span>
            </div>
            <button className="icon-btn" style={{ width: 28, height: 28 }} onClick={() => setSelected(null)}>
              <Icon name="close" size={15} />
            </button>
          </div>

          <div className="zone-score-row">
            <div>
              <div className="eyebrow">Risk Score</div>
              <div className="zone-score" style={{ color: bandForScore(selected.riskScore).color }}>
                {selected.riskScore}%
              </div>
            </div>
            <StatusPill status={selected.status} />
          </div>

          <div className="zone-metrics">
            <div className="zone-metric">
              <span className="zm-label">Rainfall (24h)</span>
              <span className="zm-value">{selected.rainfall} mm</span>
            </div>
            <div className="zone-metric">
              <span className="zm-label">Soil Moisture</span>
              <span className="zm-value">{selected.soilMoisture}%</span>
            </div>
            <div className="zone-metric">
              <span className="zm-label">Slope</span>
              <span className="zm-value">{selected.slope}°</span>
            </div>
            <div className="zone-metric">
              <span className="zm-label">Elevation</span>
              <span className="zm-value">{selected.elevation.toLocaleString()} m</span>
            </div>
          </div>

          <div className="zone-window">
            Prediction Window
            <b>{selected.predictionWindow}</b>
          </div>

          <div className="zone-panel-foot">
            <button
              className="btn btn--primary btn--block"
              onClick={() => onViewAnalysis?.(selected)}
            >
              <Icon name="trend" size={15} /> View Risk Analysis
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
