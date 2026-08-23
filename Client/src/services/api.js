// ============================================================================
// TerraSense NER — API Service Layer
// ----------------------------------------------------------------------------
// Thin async facade over the mock data. Components call these functions and
// never touch mockData directly, so swapping to a real FastAPI backend later
// only requires changing the implementations below (fetch to BASE_URL).
//
//   Example future implementation:
//     export const getRiskZones = () =>
//       fetch(`${BASE_URL}/risk-zones`).then((r) => r.json());
// ============================================================================

import {
  KPI_SUMMARY,
  RISK_ZONES,
  INCIDENT_MARKERS,
  INFRASTRUCTURE,
  AI_PREDICTION,
  WEATHER,
  ALERTS,
  ROAD_SUMMARY,
  CRITICAL_ROADS,
  EMERGENCY_PRIORITIES,
  INCIDENT_REPORTS,
  NOTIFICATIONS,
  SYSTEM_STATUS,
  REGION_META,
} from '../data/mockData';

// Base URL for the future FastAPI backend (read from Vite env when available).
export const BASE_URL = import.meta.env?.VITE_API_BASE_URL ?? '/api';

// Simulate network latency so loading states behave like production.
const LATENCY = 250;
function resolve(data, ms = LATENCY) {
  return new Promise((res) => setTimeout(() => res(structuredCloneSafe(data)), ms));
}

// structuredClone is widely available; guard for older runtimes.
function structuredCloneSafe(data) {
  try {
    return structuredClone(data);
  } catch {
    return JSON.parse(JSON.stringify(data));
  }
}

// --- Read endpoints ----------------------------------------------------------
export const getRegionMeta = () => resolve(REGION_META);
export const getKpiSummary = () => resolve(KPI_SUMMARY);
export const getRiskZones = () => resolve(RISK_ZONES);
export const getIncidentMarkers = () => resolve(INCIDENT_MARKERS);
export const getInfrastructure = () => resolve(INFRASTRUCTURE);
export const getAiPrediction = () => resolve(AI_PREDICTION);
export const getWeather = () => resolve(WEATHER);
export const getAlerts = () => resolve(ALERTS);
export const getRoadSummary = () => resolve(ROAD_SUMMARY);
export const getCriticalRoads = () => resolve(CRITICAL_ROADS);
export const getEmergencyPriorities = () => resolve(EMERGENCY_PRIORITIES);
export const getIncidentReports = () => resolve(INCIDENT_REPORTS);
export const getNotifications = () => resolve(NOTIFICATIONS);
export const getSystemStatus = () => resolve(SYSTEM_STATUS);

// --- Write endpoints ---------------------------------------------------------
// Simulates POST /incidents. Returns the created record with a server status.
export function submitIncidentReport(payload) {
  const record = {
    id: `rep-${Date.now()}`,
    ...payload,
    status: 'Pending Verification',
    receivedAt: new Date().toISOString(),
  };
  return resolve(record, 600);
}
