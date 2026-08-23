# TerraSense NER — Backend API Specification

This document defines every endpoint the **frontend** expects from the **backend**
(FastAPI), the exact JSON shape each one must return, how each field maps to the
problem statement's data sources, and how to implement them.

The frontend already talks to a single service layer at
`Client/src/services/api.js`. Every function there is a placeholder that currently
returns mock data from `Client/src/data/mockData.js`. **To go live, you only change
`api.js` to call these endpoints** — no component code changes.

---

## 1. Conventions

| Topic | Value |
|-------|-------|
| Base URL | Read from `VITE_API_BASE_URL` env var; defaults to `/api` |
| Protocol | HTTPS, JSON request/response (`Content-Type: application/json`) |
| Auth | `Authorization: Bearer <JWT>` (recommended; see §4) |
| Coordinates | Always `[latitude, longitude]` arrays (Leaflet order) |
| Risk status enum | `LOW` \| `MODERATE` \| `HIGH` \| `CRITICAL` |
| Risk score | Integer `0–100` |
| Timestamps | Return ISO-8601 UTC (see the "time" note in §5) |
| Errors | See §3 |

### Risk band thresholds (must match the UI)

| Band | Score range | Color |
|------|-------------|-------|
| `LOW` | 0–20 | Green `#22c55e` |
| `MODERATE` | 20–40 | Yellow `#eab308` |
| `HIGH` | 40–70 | Orange `#f97316` |
| `CRITICAL` | 70–100 | Red `#ef4444` |

The backend should compute `status` from `riskScore` using these exact bounds so
map colors, pills, and gauges stay consistent.

---

## 2. Endpoint summary

| # | Method | Path | Frontend function (`api.js`) | Used by |
|---|--------|------|------------------------------|---------|
| 1 | GET | `/region/meta` | `getRegionMeta` | Header |
| 2 | GET | `/kpis/summary` | `getKpiSummary` | Dashboard KPI cards |
| 3 | GET | `/risk-zones` | `getRiskZones` | Risk Map, Dashboard |
| 4 | GET | `/incidents/markers` | `getIncidentMarkers` | Risk Map |
| 5 | GET | `/infrastructure` | `getInfrastructure` | Risk Map |
| 6 | GET | `/ai/prediction` | `getAiPrediction` | AI Risk Prediction panel |
| 7 | GET | `/weather` | `getWeather` | Weather & Rainfall panel |
| 8 | GET | `/alerts` | `getAlerts` | Alerts page, Dashboard |
| 9 | GET | `/roads/summary` | `getRoadSummary` | Road Connectivity |
| 10 | GET | `/roads/critical` | `getCriticalRoads` | Road Connectivity |
| 11 | GET | `/emergency/priorities` | `getEmergencyPriorities` | Emergency Response |
| 12 | GET | `/incidents` | `getIncidentReports` | Incident table |
| 13 | POST | `/incidents` | `submitIncidentReport` | Report Incident modal |
| 14 | GET | `/notifications` | `getNotifications` | Header bell |
| 15 | GET | `/system/status` | `getSystemStatus` | System Status page |

**Optional shared filter:** every list endpoint (3, 4, 5, 8, 10, 11, 12) should
accept `?state=<NER state>` to support the header's state/district selector.
`state=All NER States` (or omitting it) returns everything.

---

## 3. Error format

Return the appropriate HTTP status and a consistent body:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Risk zone 'zone-xyz' does not exist."
  }
}
```

| Status | When |
|--------|------|
| 400 | Invalid query/body |
| 401 / 403 | Missing / invalid token |
| 404 | Unknown resource id |
| 422 | Validation error (FastAPI default) |
| 500 | Server error |

---

## 4. Authentication (recommended)

The UI has an "Administrator" profile, citizen reporting, and field officers.
Suggested flow:

- `POST /auth/login` → `{ token, user }`
- Send `Authorization: Bearer <token>` on every request.
- Roles: `admin` (full), `officer` (verify incidents), `citizen` (submit incidents only).
- Public read endpoints (risk zones, alerts) may be unauthenticated for low-network
  public dashboards; writes (`POST /incidents`, verification) require auth.

Auth is **not yet wired in the frontend** — add an interceptor in `api.js` when ready.

---

## 5. A note on time fields

The mock data uses human strings like `"8 min ago"` and `"2 min ago"`.
**Recommended:** return real ISO timestamps and let the frontend format them:

```json
{ "issuedAt": "2026-08-23T09:14:00Z" }
```

Then add a small `timeAgo()` helper on the frontend. If you prefer zero frontend
changes for the demo, you may return the pre-formatted string in the existing field
names (`issued`, `time`, `lastUpdated`). Both options are noted per-endpoint below.

---

## 6. Endpoints in detail

---

### 1. GET `/region/meta`

Region banner + default map view.

**Response 200**

```json
{
  "name": "NER",
  "lastUpdated": "2 min ago",
  "center": [25.8, 92.6],
  "zoom": 6
}
```

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | Region label shown in header. |
| `lastUpdated` | string | Recommended: send ISO `lastUpdatedAt`; frontend renders "x min ago". |
| `center` | `[lat, lng]` | Default map center (NER centroid). |
| `zoom` | int | Default Leaflet zoom. |

**Implement:** static config, or derived from the newest data-ingestion timestamp.

---

### 2. GET `/kpis/summary`

The four Risk Overview cards (value + trend sparkline + delta chip).

**Response 200**

```json
{
  "criticalZones": {
    "value": 12,
    "note": "Requires immediate attention",
    "band": "CRITICAL",
    "delta": { "dir": "up", "text": "+3 today" },
    "trend": [6, 7, 7, 8, 9, 10, 11, 12]
  },
  "highRiskZones": {
    "value": 28, "note": "Elevated across NER", "band": "HIGH",
    "delta": { "dir": "up", "text": "+7 since yesterday" },
    "trend": [18, 19, 21, 20, 23, 25, 26, 28]
  },
  "activeAlerts": {
    "value": 9, "note": "3 critical", "band": "CRITICAL",
    "delta": { "dir": "up", "text": "+2 this hour" },
    "trend": [4, 5, 5, 6, 6, 7, 8, 9]
  },
  "roadsAffected": {
    "value": 17, "note": "5 currently blocked", "band": "HIGH",
    "delta": { "dir": "flat", "text": "No change" },
    "trend": [15, 16, 16, 17, 17, 16, 17, 17]
  }
}
```

| Field | Type | Notes |
|-------|------|-------|
| `value` | int | Current count. |
| `note` | string | Sub-caption under the number. |
| `band` | enum | Card accent color (status only). |
| `delta.dir` | `"up"` \| `"down"` \| `"flat"` | Drives the change-chip icon/color. |
| `delta.text` | string | Short change description. |
| `trend` | `number[]` | Last ~8 readings for the mini sparkline. |

**Implement (aggregation queries):**
- `criticalZones` = count of risk zones with `riskScore >= 70`.
- `highRiskZones` = count with `40 <= riskScore < 70` (or `>= 40`, your call — document it).
- `activeAlerts` = count of open alerts; `delta` from last hour.
- `roadsAffected` = `roadSummary.atRisk`.
- `trend` = hourly/daily snapshots stored in a time-series table.

---

### 3. GET `/risk-zones`

Core GIS layer. Each item is a circular risk zone drawn on the map and carries the
full environmental payload behind the AI score.

**Query:** `?state=` (optional)

**Response 200** — array of:

```json
[
  {
    "id": "zone-aizawl",
    "district": "Aizawl",
    "state": "Mizoram",
    "center": [23.7271, 92.7176],
    "radius": 9000,
    "riskScore": 87,
    "status": "CRITICAL",
    "rainfall": 182,
    "soilMoisture": 89,
    "slope": 38,
    "elevation": 1240,
    "predictionWindow": "Next 6–12 hours",
    "populationExposed": 4820
  }
]
```

| Field | Type | Unit / Notes | Data source |
|-------|------|--------------|-------------|
| `id` | string | Stable zone id. | DB |
| `district`, `state` | string | Location labels. | Admin boundaries |
| `center` | `[lat, lng]` | Zone centroid. | GIS |
| `radius` | int | Meters (Leaflet `Circle`). | Zone extent / grid cell |
| `riskScore` | int 0–100 | AI output. | **ML model** |
| `status` | enum | Derived from `riskScore`. | Computed |
| `rainfall` | int | mm / 24h. | **IMD rainfall feed** |
| `soilMoisture` | int | % saturation. | **ISRO / soil sensors** |
| `slope` | int | Degrees. | **DEM / terrain analysis** |
| `elevation` | int | Meters. | **DEM** |
| `predictionWindow` | string | Human window; e.g. "Next 6–12 hours". | ML model |
| `populationExposed` | int | People in the zone. | Census / settlement layer |

**Implement:** run the landslide model per district/grid cell on each ingestion
cycle, persist the scored zones, and serve them here. `GeoJSON` is also acceptable
if you later switch the map to polygons — keep `[lat,lng]` + `radius` for now.

---

### 4. GET `/incidents/markers`

Lightweight incident pins for the map (distinct from the full report table).

**Response 200**

```json
[
  { "id": "inc-1", "type": "Soil Crack", "location": "Aizawl", "coords": [23.735, 92.71], "severity": "HIGH" },
  { "id": "inc-2", "type": "Road Blockage", "location": "Champhai", "coords": [23.47, 93.33], "severity": "CRITICAL" }
]
```

| Field | Type | Notes |
|-------|------|-------|
| `type` | string | One of the incident types (see §7). |
| `coords` | `[lat, lng]` | Pin location. |
| `severity` | enum | Marker color. |

**Implement:** the most recent/active verified incidents that have coordinates.
Can be a filtered projection of the incidents table (§12).

---

### 5. GET `/infrastructure`

Critical infrastructure pins (hospitals, relief depots, command posts).

**Response 200**

```json
[
  { "id": "infra-1", "name": "Aizawl Civil Hospital", "type": "Hospital", "coords": [23.728, 92.719] },
  { "id": "infra-2", "name": "Gangtok Relief Depot", "type": "Relief Depot", "coords": [27.335, 88.61] }
]
```

**Implement:** static reference dataset of key facilities per district.

---

### 6. GET `/ai/prediction`

Detailed AI output for the AI Risk Prediction panel (gauge, factors, 24h trend).

**Query:** `?zoneId=zone-aizawl` or `?district=Aizawl` (optional; defaults to the
highest-risk zone).

**Response 200**

```json
{
  "district": "Aizawl",
  "state": "Mizoram",
  "riskScore": 87,
  "status": "CRITICAL",
  "summary": "High probability of slope failure within the next 6–12 hours.",
  "predictionWindow": "Next 6–12 hours",
  "factors": [
    { "name": "Heavy Rainfall", "level": "High", "weight": 0.90 },
    { "name": "Soil Moisture", "level": "Very High", "weight": 0.95 },
    { "name": "Slope", "level": "38°", "weight": 0.82 },
    { "name": "Historical Activity", "level": "High", "weight": 0.78 },
    { "name": "Terrain Stability", "level": "Low", "weight": 0.85 }
  ],
  "trend": [
    { "time": "00:00", "risk": 41 },
    { "time": "02:00", "risk": 44 },
    { "time": "22:00", "risk": 87 }
  ]
}
```

| Field | Type | Notes |
|-------|------|-------|
| `riskScore` / `status` | int / enum | Same semantics as risk zones. |
| `summary` | string | One-line plain-language prediction. |
| `predictionWindow` | string | Expected time window. |
| `factors[]` | array | Model feature contributions. |
| `factors[].name` | string | Feature label. |
| `factors[].level` | string | Human label ("High", "38°", "Very High"). |
| `factors[].weight` | float 0–1 | Bar fill fraction (feature importance / SHAP). |
| `trend[]` | array | 24h series; `time` label + `risk` 0–100. |

**Implement:**
- `weight` maps well to **feature importances** or normalized **SHAP values** from
  the model for that zone.
- `trend` = the model re-scored at 2-hour steps over the last 24h (store the series).
- `summary` can be templated from `status` + `predictionWindow`.

---

### 7. GET `/weather`

Current conditions + 12-hour rainfall forecast for the Weather panel.

**Query:** `?district=Aizawl` (optional)

**Response 200**

```json
{
  "district": "Aizawl",
  "temperature": 24,
  "humidity": 91,
  "rainfall": 42,
  "wind": 18,
  "warning": "Heavy rainfall expected for the next 8 hours",
  "forecast": [
    { "time": "Now", "rain": 42 },
    { "time": "+1h", "rain": 46 },
    { "time": "+11h", "rain": 16 }
  ]
}
```

| Field | Type | Unit | Notes |
|-------|------|------|-------|
| `temperature` | int | °C | |
| `humidity` | int | % | |
| `rainfall` | int | mm/hr | Current intensity. |
| `wind` | int | km/h | |
| `warning` | string \| null | | Show banner when present. |
| `forecast[]` | array | | `time` label + `rain` mm/hr per hour. |

**Implement:** proxy IMD / a weather provider; cache per district. The `warning`
is set when forecast rainfall crosses your alert threshold.

---

### 8. GET `/alerts`

Active early warnings.

**Query:** `?state=`, optional `?status=CRITICAL|HIGH`

**Response 200**

```json
[
  {
    "id": "alert-1",
    "district": "Aizawl District",
    "state": "Mizoram",
    "probability": 91,
    "issued": "12 min ago",
    "status": "CRITICAL",
    "message": "Imminent slope failure risk. Evacuation warning recommended for low-lying settlements."
  }
]
```

| Field | Type | Notes |
|-------|------|-------|
| `probability` | int 0–100 | Landslide probability. |
| `issued` | string | Recommended: ISO `issuedAt` (see §5). |
| `status` | enum | Severity. |
| `message` | string | Human guidance. |

**Implement:** created when a zone crosses the alert threshold; store `issuedAt`,
`expiresAt`, and a `resolved` flag. This endpoint returns unresolved alerts,
newest first.

---

### 9. GET `/roads/summary`

Road-network status counters.

**Response 200**

```json
{ "open": 126, "restricted": 11, "blocked": 5, "atRisk": 17 }
```

| Field | Type | Notes |
|-------|------|-------|
| `open` / `restricted` / `blocked` | int | Counts by state. |
| `atRisk` | int | Restricted + blocked + monitored (feeds the "Roads Affected" KPI). |

**Implement:** aggregate over the roads table.

---

### 10. GET `/roads/critical`

The critical roads list.

**Query:** `?state=`

**Response 200**

```json
[
  { "id": "road-1", "name": "NH-6", "status": "BLOCKED", "band": "CRITICAL", "note": "Debris slide near km 42", "coords": [23.7, 92.9] },
  { "id": "road-3", "name": "NH-10", "status": "RESTRICTED", "band": "MODERATE", "note": "Single-lane movement", "coords": [27.3, 88.5] }
]
```

| Field | Type | Notes |
|-------|------|-------|
| `status` | string | Display label: `BLOCKED` \| `HIGH RISK` \| `RESTRICTED`. |
| `band` | enum | Color band for the pill (`CRITICAL`/`HIGH`/`MODERATE`). |
| `note` | string | Short condition note. |
| `coords` | `[lat, lng]` | For "View on Map". |

> **Contract detail:** the UI shows `status` text but colors it using `band`.
> Keep both fields. Suggested mapping: BLOCKED→CRITICAL, HIGH RISK→HIGH,
> RESTRICTED→MODERATE.

**Implement:** roads flagged by proximity to critical/high zones or by field reports.

---

### 11. GET `/emergency/priorities`

Ranked emergency-response queue.

**Query:** `?state=`

**Response 200**

```json
[
  {
    "id": "pri-1",
    "rank": 1,
    "district": "Aizawl District",
    "state": "Mizoram",
    "risk": 94,
    "populationExposed": 4820,
    "roadStatus": "Blocked",
    "action": "Deploy response team and issue evacuation warning.",
    "status": "CRITICAL"
  }
]
```

| Field | Type | Notes |
|-------|------|-------|
| `rank` | int | 1 = highest priority; array pre-sorted ascending. |
| `risk` | int 0–100 | Zone risk. |
| `populationExposed` | int | People affected. |
| `roadStatus` | string | `Open` \| `Restricted` \| `Blocked`. |
| `action` | string | Recommended action text. |
| `status` | enum | Severity band. |

**Implement (priority score):** rank by a weighted function, e.g.
`priority = risk * w1 + normalizedPopulation * w2 + roadPenalty * w3`.
Document the weights. Sort descending and assign `rank`.

---

### 12. GET `/incidents`

Full incident report table (geo-tagged ground truth).

**Query:** `?status=Pending|Verified`, `?severity=CRITICAL|HIGH`, `?state=`,
pagination `?page=&limit=` (frontend currently filters client-side; server-side
filters are a bonus).

**Response 200**

```json
[
  {
    "id": "rep-1",
    "location": "Aizawl",
    "incident": "Soil Crack",
    "severity": "HIGH",
    "source": "Field Officer",
    "time": "8 min ago",
    "status": "Verified"
  }
]
```

| Field | Type | Notes |
|-------|------|-------|
| `location` | string | District/place name. |
| `incident` | string | One of the incident types (§7 list below). |
| `severity` | enum | `LOW`/`MODERATE`/`HIGH`/`CRITICAL`. |
| `source` | string | `Field Officer` \| `Citizen`. |
| `time` | string | Recommended: ISO `createdAt` (see §5). |
| `status` | string | `Pending` \| `Verified`. |

**Implement:** newest first. This table is populated by `POST /incidents` (§13)
plus officer verification.

---

### 13. POST `/incidents`

Submit a geo-tagged incident report (Report Incident modal — citizens & field officers).

**Request body**

```json
{
  "incident": "Landslide",
  "severity": "HIGH",
  "source": "Citizen",
  "location": "23.7271, 92.7176",
  "coords": { "lat": 23.7271, "lng": 92.7176 },
  "description": "Cracks widening along the hillside road.",
  "photo": "photo-filename.jpg",
  "video": null
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `incident` | enum | yes | Landslide, Road Blockage, Soil Crack, Slope Movement, Flooding. |
| `severity` | enum | no | Defaults to `HIGH` on the frontend if omitted. |
| `source` | string | yes | `Citizen` / `Field Officer`. |
| `location` | string | yes | "lat, lng" display string. |
| `coords` | `{lat,lng}` | yes | Captured via browser geolocation. |
| `description` | string | no | Free text. |
| `photo` / `video` | string \| null | no | See file-upload note. |

> **File uploads:** the frontend currently sends the file **name** only. For real
> media, switch to `multipart/form-data` (fields + `photo`/`video` file parts) or a
> pre-signed upload URL flow, and return stored file URLs.

**Response 201** — the created record (frontend shows a success panel with these):

```json
{
  "id": "rep-1755940000000",
  "incident": "Landslide",
  "severity": "HIGH",
  "source": "Citizen",
  "location": "23.7271, 92.7176",
  "coords": { "lat": 23.7271, "lng": 92.7176 },
  "description": "Cracks widening along the hillside road.",
  "status": "Pending Verification",
  "receivedAt": "2026-08-23T09:20:00Z"
}
```

| Field | Notes |
|-------|-------|
| `id` | Server-generated id (frontend shows it as the reference number). |
| `status` | Must be `"Pending Verification"` for the success screen text. |
| `receivedAt` | ISO timestamp. |

**Implement:** validate, persist as `Pending`, return the record. New reports then
appear in `GET /incidents` and (once verified with coords) in `/incidents/markers`.

---

### 14. GET `/notifications`

Header notification dropdown.

**Response 200**

```json
[
  { "id": "n1", "title": "Critical alert issued — Aizawl", "time": "12 min ago", "band": "CRITICAL" },
  { "id": "n3", "title": "New citizen report — Champhai", "time": "16 min ago", "band": "HIGH" }
]
```

| Field | Type | Notes |
|-------|------|-------|
| `title` | string | Notification text. |
| `time` | string | Recommended: ISO `createdAt`. |
| `band` | enum | Color accent (`CRITICAL`/`HIGH`/...). |

**Implement:** an events/notifications table fed by alert + incident + threshold
events. The bell badge count = number of unread items.

---

### 15. GET `/system/status`

System Status page — sensing network, feeds, model, network mode.

**Response 200**

```json
{
  "overall": "Operational",
  "sensors": { "online": 214, "total": 226 },
  "aiModel": "v3.2 · Nowcast",
  "dataFeeds": [
    { "name": "Rainfall (IMD)", "status": "Live" },
    { "name": "Soil Moisture (ISRO)", "status": "Live" },
    { "name": "Satellite Imagery", "status": "Live" },
    { "name": "Terrain / DEM", "status": "Cached" }
  ],
  "network": "Low-bandwidth mode available"
}
```

| Field | Type | Notes |
|-------|------|-------|
| `overall` | string | `Operational` / `Degraded` / `Down`. |
| `sensors` | `{online,total}` | Sensor health. |
| `aiModel` | string | Model version label. |
| `dataFeeds[]` | array | Per-feed `status`: `Live` / `Cached` / `Down`. |
| `network` | string | Connectivity note. |

**Implement:** health checks / heartbeats for each ingestion pipeline and sensor
gateway.

---

## 7. Reference enums (frontend-owned, optional to serve)

These are constants the frontend already knows; you do **not** need endpoints for
them, but serving them lets you change options without a frontend release.

- **NER states:** `All NER States, Assam, Arunachal Pradesh, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim, Tripura`
- **Incident types:** `Landslide, Road Blockage, Soil Crack, Slope Movement, Flooding`
- **Risk bands:** see §1.

Optional endpoint: `GET /meta/enums` returning all of the above.

---

## 8. How the frontend consumes these (wiring guide)

1. **Set the base URL** — create `Client/.env`:

   ```
   VITE_API_BASE_URL=https://api.terrasense.example/api
   ```

2. **Swap the mock functions** in `Client/src/services/api.js`. Example:

   ```js
   export const BASE_URL = import.meta.env?.VITE_API_BASE_URL ?? '/api';

   async function get(path) {
     const res = await fetch(`${BASE_URL}${path}`, {
       headers: { Accept: 'application/json' },
       // credentials: 'include', // if using cookie auth
     });
     if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
     return res.json();
   }

   export const getRegionMeta        = () => get('/region/meta');
   export const getKpiSummary        = () => get('/kpis/summary');
   export const getRiskZones         = () => get('/risk-zones');
   export const getIncidentMarkers   = () => get('/incidents/markers');
   export const getInfrastructure    = () => get('/infrastructure');
   export const getAiPrediction      = (zoneId) => get(`/ai/prediction${zoneId ? `?zoneId=${zoneId}` : ''}`);
   export const getWeather           = (district) => get(`/weather${district ? `?district=${encodeURIComponent(district)}` : ''}`);
   export const getAlerts            = () => get('/alerts');
   export const getRoadSummary       = () => get('/roads/summary');
   export const getCriticalRoads     = () => get('/roads/critical');
   export const getEmergencyPriorities = () => get('/emergency/priorities');
   export const getIncidentReports   = () => get('/incidents');
   export const getNotifications     = () => get('/notifications');
   export const getSystemStatus      = () => get('/system/status');

   export async function submitIncidentReport(payload) {
     const res = await fetch(`${BASE_URL}/incidents`, {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify(payload),
     });
     if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
     return res.json();
   }
   ```

   Because every component already imports from `api.js`, the whole app switches to
   live data with just this file changed.

3. **CORS:** enable the frontend origin on the FastAPI side (see §9).

---

## 9. FastAPI implementation skeleton

```python
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(title="TerraSense NER API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://your-frontend"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Schemas ----
class RiskZone(BaseModel):
    id: str
    district: str
    state: str
    center: list[float]          # [lat, lng]
    radius: int
    riskScore: int
    status: str                  # LOW|MODERATE|HIGH|CRITICAL
    rainfall: int
    soilMoisture: int
    slope: int
    elevation: int
    predictionWindow: str
    populationExposed: int

class IncidentIn(BaseModel):
    incident: str
    severity: Optional[str] = "HIGH"
    source: str
    location: str
    coords: dict                 # {"lat":..,"lng":..}
    description: Optional[str] = None
    photo: Optional[str] = None
    video: Optional[str] = None

def band_for_score(score: int) -> str:
    if score >= 70: return "CRITICAL"
    if score >= 40: return "HIGH"
    if score >= 20: return "MODERATE"
    return "LOW"

# ---- Routes ----
@app.get("/api/risk-zones", response_model=List[RiskZone])
def risk_zones(state: Optional[str] = Query(None)):
    zones = query_scored_zones(state)   # your DB/model layer
    for z in zones:
        z["status"] = band_for_score(z["riskScore"])
    return zones

@app.post("/api/incidents", status_code=201)
def create_incident(body: IncidentIn):
    record = save_incident(body)        # persist as "Pending Verification"
    return record
```

---

## 10. Mapping to the problem statement (data → endpoint)

| Problem-statement requirement | Where it surfaces |
|-------------------------------|-------------------|
| Analyse rainfall patterns | `risk-zones.rainfall`, `weather` |
| Analyse soil moisture | `risk-zones.soilMoisture` |
| Analyse satellite imagery | model input → `risk-zones.riskScore`, `system/status` feed |
| Analyse terrain & slope | `risk-zones.slope`, `risk-zones.elevation` |
| Historical landslide records | `ai/prediction.factors` ("Historical Activity") |
| AI/ML landslide prediction | `risk-zones.riskScore`, `ai/prediction` |
| Real-time alerts | `alerts`, `notifications` |
| GIS vulnerable-zone visualization | `risk-zones`, `incidents/markers`, `infrastructure` |
| Geo-tagged incident reporting | `POST /incidents`, `GET /incidents` |
| Road connectivity | `roads/summary`, `roads/critical` |
| Weather-linked risk forecasts | `weather`, `ai/prediction.trend` |
| Emergency response prioritisation | `emergency/priorities` |
| Multilingual communication | alert/notification text; add `?lang=` later |
| Low-network operation | `system/status.network`; keep payloads small, cache-friendly |

---

_Generated for the TerraSense NER frontend. The response shapes above match
`Client/src/data/mockData.js` exactly, so the UI renders identically when the
backend returns this contract._
