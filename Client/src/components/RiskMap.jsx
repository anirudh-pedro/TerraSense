import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Circle, CircleMarker, Tooltip, Popup, LayersControl, useMap } from 'react-leaflet';
import Icon from './Icon';
import StatusPill from './StatusPill';
import { RISK_BANDS, bandForScore, REGION_META } from '../data/mockData';

const LEGEND = [
  { band: RISK_BANDS.LOW, label: 'Low', range: '0–20%' },
  { band: RISK_BANDS.MODERATE, label: 'Moderate', range: '20–40%' },
  { band: RISK_BANDS.HIGH, label: 'High', range: '40–70%' },
  { band: RISK_BANDS.CRITICAL, label: 'Critical', range: '70–100%' },
];

const STATE_COORDS = {
  'Assam': [26.2006, 92.9376],
  'Arunachal Pradesh': [28.2180, 94.7278],
  'Manipur': [24.6637, 93.9063],
  'Meghalaya': [25.4670, 91.3662],
  'Mizoram': [23.1645, 92.9376],
  'Nagaland': [26.1584, 94.5624],
  'Sikkim': [27.5330, 88.5122],
  'Tripura': [23.9408, 91.9882],
  'All NER States': REGION_META.center
};

function MapEffect({ selectedState }) {
  const map = useMap();
  useEffect(() => {
    const coords = STATE_COORDS[selectedState] || REGION_META.center;
    const zoom = selectedState === 'All NER States' ? REGION_META.zoom : 7;
    map.flyTo(coords, zoom, { duration: 1.5 });
  }, [selectedState, map]);
  return null;
}

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
  selectedState = 'All NER States',
}) {
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
        maxBounds={[[21.5, 89.0], [29.5, 97.5]]}
        maxBoundsViscosity={1.0}
        minZoom={6}
      >
        <MapResizer />
        <MapEffect selectedState={selectedState} />
        <LayersControl position="topleft">

          <LayersControl.BaseLayer checked name="Clean Map (Auto Labels)">
            <>
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}{r}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
              />
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png"
                minZoom={8}
                pane="markerPane"
              />
            </>
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="Satellite (Auto Labels)">
            <>
              <TileLayer
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                attribution='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
              />
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png"
                minZoom={8}
                pane="markerPane"
              />
            </>
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
              eventHandlers={{
                mouseover: (e) => {
                  e.target.setStyle({ weight: 3, fillOpacity: Math.min(1, zoneStyle(z.riskScore).fillOpacity + 0.2) });
                },
                mouseout: (e) => {
                  e.target.setStyle(zoneStyle(z.riskScore));
                }
              }}
            >
              <Tooltip direction="top" opacity={1}>
                <b>{z.district}</b> — Click for Risk Prediction
              </Tooltip>
              <Popup className="custom-popup" closeButton={false}>
                <div className="pop-header">
                  <div className="pop-title">Risk Prediction</div>
                  <div className="pop-loc">{z.district}, {z.state}</div>
                </div>
                <div className="pop-score-row">
                  <div className="pop-score" style={{ color: bandForScore(z.riskScore).color }}>
                    {z.riskScore}%
                  </div>
                  <StatusPill status={z.status} />
                </div>
                <div className="pop-summary">
                  {z.status === 'CRITICAL' ? 'High probability of slope failure within the prediction window.' :
                   z.status === 'HIGH' ? 'Elevated slope instability and saturated soil. Monitor closely.' :
                   'Risk levels are currently manageable but subject to change.'}
                </div>
                
                <div className="pop-factors">
                  <div className="pop-factor-title">Risk Factors</div>
                  <div className="pop-factor-row">
                    <span>Heavy Rainfall</span>
                    <b>{z.rainfall > 120 ? 'High' : z.rainfall > 80 ? 'Moderate' : 'Low'}</b>
                  </div>
                  <div className="pop-factor-row">
                    <span>Soil Moisture</span>
                    <b>{z.soilMoisture > 80 ? 'Very High' : z.soilMoisture > 60 ? 'High' : 'Moderate'}</b>
                  </div>
                  <div className="pop-factor-row">
                    <span>Slope</span>
                    <b>{z.slope}°</b>
                  </div>
                  <div className="pop-factor-row">
                    <span>Terrain Stability</span>
                    <b>{z.riskScore > 75 ? 'Low' : z.riskScore > 50 ? 'Moderate' : 'High'}</b>
                  </div>
                </div>

                <div className="pop-window">
                  Prediction Window
                  <b>{z.predictionWindow}</b>
                </div>
              </Popup>
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


    </div>
  );
}
