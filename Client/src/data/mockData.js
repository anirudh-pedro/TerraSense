// ============================================================================
// TerraSense NER — Mock Data Layer
// ----------------------------------------------------------------------------
// Realistic mock data structured to mirror a future FastAPI backend.
// Every export here maps to an eventual API resource (see services/api.js).
// Replace these with live API responses without changing component code.
// ============================================================================

// --- Risk band definitions (single source of truth for colors + labels) -----
export const RISK_BANDS = {
  LOW: { key: 'LOW', label: 'Low', color: '#22c55e', range: '0–20%', min: 0, max: 20 },
  MODERATE: { key: 'MODERATE', label: 'Moderate', color: '#eab308', range: '20–40%', min: 20, max: 40 },
  HIGH: { key: 'HIGH', label: 'High', color: '#f97316', range: '40–70%', min: 40, max: 70 },
  CRITICAL: { key: 'CRITICAL', label: 'Critical', color: '#ef4444', range: '70–100%', min: 70, max: 100 },
};

// Given a 0-100 risk score, return the matching band object.
export function bandForScore(score) {
  if (score >= 70) return RISK_BANDS.CRITICAL;
  if (score >= 40) return RISK_BANDS.HIGH;
  if (score >= 20) return RISK_BANDS.MODERATE;
  return RISK_BANDS.LOW;
}

// --- NER states used by the state/district selector --------------------------
export const NER_STATES = [
  'All NER States',
  'Assam',
  'Arunachal Pradesh',
  'Manipur',
  'Meghalaya',
  'Mizoram',
  'Nagaland',
  'Sikkim',
  'Tripura',
];

// --- Region meta -------------------------------------------------------------
export const REGION_META = {
  name: 'NER',
  lastUpdated: '2 min ago',
  center: [25.8, 92.6],
  zoom: 6,
};

// --- KPI summary (Risk Overview cards) --------------------------------------
// `trend` powers the mini sparkline; `delta` powers the change chip.
export const KPI_SUMMARY = {
  criticalZones: {
    value: 12,
    note: 'Requires immediate attention',
    band: 'CRITICAL',
    delta: { dir: 'up', text: '+3 today' },
    trend: [6, 7, 7, 8, 9, 10, 11, 12],
  },
  highRiskZones: {
    value: 28,
    note: 'Elevated across NER',
    band: 'HIGH',
    delta: { dir: 'up', text: '+7 since yesterday' },
    trend: [18, 19, 21, 20, 23, 25, 26, 28],
  },
  activeAlerts: {
    value: 9,
    note: '3 critical',
    band: 'CRITICAL',
    delta: { dir: 'up', text: '+2 this hour' },
    trend: [4, 5, 5, 6, 6, 7, 8, 9],
  },
  roadsAffected: {
    value: 17,
    note: '5 currently blocked',
    band: 'HIGH',
    delta: { dir: 'flat', text: 'No change' },
    trend: [15, 16, 16, 17, 17, 16, 17, 17],
  },
};

// --- Risk zones (drawn on the GIS map) --------------------------------------
// Each zone carries the full environmental payload the AI model consumes.
export const RISK_ZONES = [
  {
    id: 'zone-aizawl',
    district: 'Aizawl',
    state: 'Mizoram',
    center: [23.7271, 92.7176],
    radius: 9000,
    riskScore: 87,
    status: 'CRITICAL',
    rainfall: 182,
    soilMoisture: 89,
    slope: 38,
    elevation: 1240,
    predictionWindow: 'Next 6–12 hours',
    populationExposed: 4820,
  },
  {
    id: 'zone-champhai',
    district: 'Champhai',
    state: 'Mizoram',
    center: [23.4739, 93.3295],
    radius: 7000,
    riskScore: 74,
    status: 'CRITICAL',
    rainfall: 141,
    soilMoisture: 81,
    slope: 34,
    elevation: 1310,
    predictionWindow: 'Next 12–24 hours',
    populationExposed: 2140,
  },
  {
    id: 'zone-kohima',
    district: 'Kohima',
    state: 'Nagaland',
    center: [25.6751, 94.1086],
    radius: 8000,
    riskScore: 68,
    status: 'HIGH',
    rainfall: 118,
    soilMoisture: 76,
    slope: 31,
    elevation: 1444,
    predictionWindow: 'Next 24 hours',
    populationExposed: 3110,
  },
  {
    id: 'zone-shillong',
    district: 'East Khasi Hills',
    state: 'Meghalaya',
    center: [25.5788, 91.8933],
    radius: 8500,
    riskScore: 58,
    status: 'HIGH',
    rainfall: 96,
    soilMoisture: 72,
    slope: 27,
    elevation: 1496,
    predictionWindow: 'Next 24–36 hours',
    populationExposed: 5200,
  },
  {
    id: 'zone-itanagar',
    district: 'Papum Pare',
    state: 'Arunachal Pradesh',
    center: [27.0844, 93.6053],
    radius: 9500,
    riskScore: 63,
    status: 'HIGH',
    rainfall: 108,
    soilMoisture: 74,
    slope: 33,
    elevation: 620,
    predictionWindow: 'Next 24 hours',
    populationExposed: 2760,
  },
  {
    id: 'zone-gangtok',
    district: 'Gangtok',
    state: 'Sikkim',
    center: [27.3389, 88.6065],
    radius: 7500,
    riskScore: 79,
    status: 'CRITICAL',
    rainfall: 156,
    soilMoisture: 85,
    slope: 41,
    elevation: 1650,
    predictionWindow: 'Next 6–12 hours',
    populationExposed: 3980,
  },
  {
    id: 'zone-imphal',
    district: 'Imphal East',
    state: 'Manipur',
    center: [24.817, 93.9368],
    radius: 7000,
    riskScore: 34,
    status: 'MODERATE',
    rainfall: 52,
    soilMoisture: 58,
    slope: 19,
    elevation: 786,
    predictionWindow: 'Next 48 hours',
    populationExposed: 1240,
  },
  {
    id: 'zone-guwahati',
    district: 'Kamrup Metro',
    state: 'Assam',
    center: [26.1445, 91.7362],
    radius: 9000,
    riskScore: 41,
    status: 'HIGH',
    rainfall: 68,
    soilMoisture: 64,
    slope: 15,
    elevation: 55,
    predictionWindow: 'Next 36 hours',
    populationExposed: 6100,
  },
  {
    id: 'zone-agartala',
    district: 'West Tripura',
    state: 'Tripura',
    center: [23.8315, 91.2868],
    radius: 7000,
    riskScore: 18,
    status: 'LOW',
    rainfall: 24,
    soilMoisture: 44,
    slope: 9,
    elevation: 22,
    predictionWindow: 'Stable',
    populationExposed: 320,
  },
];

// --- Incident markers on the map --------------------------------------------
export const INCIDENT_MARKERS = [
  { id: 'inc-1', type: 'Soil Crack', location: 'Aizawl', coords: [23.735, 92.71], severity: 'HIGH' },
  { id: 'inc-2', type: 'Road Blockage', location: 'Champhai', coords: [23.47, 93.33], severity: 'CRITICAL' },
  { id: 'inc-3', type: 'Slope Movement', location: 'Kohima', coords: [25.67, 94.11], severity: 'HIGH' },
  { id: 'inc-4', type: 'Landslide', location: 'Gangtok', coords: [27.34, 88.61], severity: 'CRITICAL' },
];

// --- Critical infrastructure markers ----------------------------------------
export const INFRASTRUCTURE = [
  { id: 'infra-1', name: 'Aizawl Civil Hospital', type: 'Hospital', coords: [23.728, 92.719] },
  { id: 'infra-2', name: 'Gangtok Relief Depot', type: 'Relief Depot', coords: [27.335, 88.61] },
  { id: 'infra-3', name: 'Kohima Emergency Ops', type: 'Command', coords: [25.676, 94.107] },
];

// --- AI prediction detail (for the selected / default critical zone) ---------
export const AI_PREDICTION = {
  district: 'Aizawl',
  state: 'Mizoram',
  riskScore: 87,
  status: 'CRITICAL',
  summary: 'High probability of slope failure within the next 6–12 hours.',
  predictionWindow: 'Next 6–12 hours',
  factors: [
    { name: 'Heavy Rainfall', level: 'High', weight: 0.9 },
    { name: 'Soil Moisture', level: 'Very High', weight: 0.95 },
    { name: 'Slope', level: '38°', weight: 0.82 },
    { name: 'Historical Activity', level: 'High', weight: 0.78 },
    { name: 'Terrain Stability', level: 'Low', weight: 0.85 },
  ],
  // 24h risk trend (hourly), values are 0-100 risk score
  trend: [
    { time: '00:00', risk: 41 },
    { time: '02:00', risk: 44 },
    { time: '04:00', risk: 48 },
    { time: '06:00', risk: 52 },
    { time: '08:00', risk: 57 },
    { time: '10:00', risk: 61 },
    { time: '12:00', risk: 66 },
    { time: '14:00', risk: 70 },
    { time: '16:00', risk: 74 },
    { time: '18:00', risk: 79 },
    { time: '20:00', risk: 83 },
    { time: '22:00', risk: 87 },
  ],
};

// --- Weather & rainfall ------------------------------------------------------
export const WEATHER = {
  district: 'Aizawl',
  temperature: 24,
  humidity: 91,
  rainfall: 42, // mm/hr
  wind: 18, // km/h
  warning: 'Heavy rainfall expected for the next 8 hours',
  // 12h rainfall forecast (mm/hr)
  forecast: [
    { time: 'Now', rain: 42 },
    { time: '+1h', rain: 46 },
    { time: '+2h', rain: 51 },
    { time: '+3h', rain: 48 },
    { time: '+4h', rain: 55 },
    { time: '+5h', rain: 59 },
    { time: '+6h', rain: 53 },
    { time: '+7h', rain: 44 },
    { time: '+8h', rain: 38 },
    { time: '+9h', rain: 29 },
    { time: '+10h', rain: 21 },
    { time: '+11h', rain: 16 },
  ],
};

// --- Active early warnings ---------------------------------------------------
export const ALERTS = [
  {
    id: 'alert-1',
    district: 'Aizawl District',
    state: 'Mizoram',
    probability: 91,
    issued: '12 min ago',
    status: 'CRITICAL',
    message: 'Imminent slope failure risk. Evacuation warning recommended for low-lying settlements.',
  },
  {
    id: 'alert-2',
    district: 'Champhai District',
    state: 'Mizoram',
    probability: 74,
    issued: '28 min ago',
    status: 'HIGH',
    message: 'Saturated soil and continued rainfall. Restrict movement on hill roads.',
  },
  {
    id: 'alert-3',
    district: 'Kohima District',
    state: 'Nagaland',
    probability: 68,
    issued: '41 min ago',
    status: 'HIGH',
    message: 'Elevated slope instability. Field inspection advised.',
  },
  {
    id: 'alert-4',
    district: 'Gangtok District',
    state: 'Sikkim',
    probability: 82,
    issued: '54 min ago',
    status: 'CRITICAL',
    message: 'Heavy rainfall over fragile terrain. Pre-position response teams.',
  },
  {
    id: 'alert-5',
    district: 'East Khasi Hills',
    state: 'Meghalaya',
    probability: 57,
    issued: '1 hr ago',
    status: 'HIGH',
    message: 'Rising soil moisture near NH corridor. Monitor closely.',
  },
];

// --- Road connectivity -------------------------------------------------------
export const ROAD_SUMMARY = { open: 126, restricted: 11, blocked: 5, atRisk: 17 };

export const CRITICAL_ROADS = [
  { id: 'road-1', name: 'NH-6', status: 'BLOCKED', band: 'CRITICAL', note: 'Debris slide near km 42', coords: [23.7, 92.9] },
  { id: 'road-2', name: 'Aizawl–Champhai Road', status: 'HIGH RISK', band: 'HIGH', note: 'Cracks on carriageway', coords: [23.6, 93.0] },
  { id: 'road-3', name: 'NH-10', status: 'RESTRICTED', band: 'MODERATE', note: 'Single-lane movement', coords: [27.3, 88.5] },
  { id: 'road-4', name: 'NH-2 (Kohima Bypass)', status: 'HIGH RISK', band: 'HIGH', note: 'Slope monitoring active', coords: [25.66, 94.1] },
  { id: 'road-5', name: 'Shillong–Jowai Road', status: 'RESTRICTED', band: 'MODERATE', note: 'Water logging', coords: [25.5, 92.0] },
];

// --- Emergency response priorities ------------------------------------------
export const EMERGENCY_PRIORITIES = [
  {
    id: 'pri-1',
    rank: 1,
    district: 'Aizawl District',
    state: 'Mizoram',
    risk: 94,
    populationExposed: 4820,
    roadStatus: 'Blocked',
    action: 'Deploy response team and issue evacuation warning.',
    status: 'CRITICAL',
  },
  {
    id: 'pri-2',
    rank: 2,
    district: 'Champhai District',
    state: 'Mizoram',
    risk: 78,
    populationExposed: 2140,
    roadStatus: 'Restricted',
    action: 'Deploy field inspection team.',
    status: 'CRITICAL',
  },
  {
    id: 'pri-3',
    rank: 3,
    district: 'Gangtok District',
    state: 'Sikkim',
    risk: 79,
    populationExposed: 3980,
    roadStatus: 'Restricted',
    action: 'Pre-position relief supplies and alert local authorities.',
    status: 'CRITICAL',
  },
  {
    id: 'pri-4',
    rank: 4,
    district: 'Kohima District',
    state: 'Nagaland',
    risk: 68,
    populationExposed: 3110,
    roadStatus: 'Open',
    action: 'Maintain monitoring and ready standby teams.',
    status: 'HIGH',
  },
];

// --- Incident reports (table) ------------------------------------------------
export const INCIDENT_REPORTS = [
  {
    id: 'rep-1',
    location: 'Aizawl',
    incident: 'Soil Crack',
    severity: 'HIGH',
    source: 'Field Officer',
    time: '8 min ago',
    status: 'Verified',
  },
  {
    id: 'rep-2',
    location: 'Champhai',
    incident: 'Road Blockage',
    severity: 'CRITICAL',
    source: 'Citizen',
    time: '16 min ago',
    status: 'Pending',
  },
  {
    id: 'rep-3',
    location: 'Kohima',
    incident: 'Slope Movement',
    severity: 'HIGH',
    source: 'Field Officer',
    time: '31 min ago',
    status: 'Verified',
  },
  {
    id: 'rep-4',
    location: 'Gangtok',
    incident: 'Landslide',
    severity: 'CRITICAL',
    source: 'Citizen',
    time: '47 min ago',
    status: 'Pending',
  },
  {
    id: 'rep-5',
    location: 'East Khasi Hills',
    incident: 'Flooding',
    severity: 'MODERATE',
    source: 'Field Officer',
    time: '1 hr ago',
    status: 'Verified',
  },
  {
    id: 'rep-6',
    location: 'Papum Pare',
    incident: 'Road Blockage',
    severity: 'HIGH',
    source: 'Citizen',
    time: '1 hr ago',
    status: 'Pending',
  },
];

export const INCIDENT_TYPES = ['Landslide', 'Road Blockage', 'Soil Crack', 'Slope Movement', 'Flooding'];

// --- Notifications -----------------------------------------------------------
export const NOTIFICATIONS = [
  { id: 'n1', title: 'Critical alert issued — Aizawl', time: '12 min ago', band: 'CRITICAL' },
  { id: 'n2', title: 'NH-6 reported blocked', time: '24 min ago', band: 'CRITICAL' },
  { id: 'n3', title: 'New citizen report — Champhai', time: '16 min ago', band: 'HIGH' },
  { id: 'n4', title: 'Rainfall threshold exceeded — Gangtok', time: '38 min ago', band: 'HIGH' },
];

// --- System status -----------------------------------------------------------
export const SYSTEM_STATUS = {
  overall: 'Operational',
  sensors: { online: 214, total: 226 },
  aiModel: 'v3.2 · Nowcast',
  dataFeeds: [
    { name: 'Rainfall (IMD)', status: 'Live' },
    { name: 'Soil Moisture (ISRO)', status: 'Live' },
    { name: 'Satellite Imagery', status: 'Live' },
    { name: 'Terrain / DEM', status: 'Cached' },
  ],
  network: 'Low-bandwidth mode available',
};
