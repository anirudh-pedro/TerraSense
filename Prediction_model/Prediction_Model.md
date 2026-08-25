# AI Prediction Service — Usage Guide

Documentation for `ai_prediction_service.py`, the module implementing
`GET /ai/prediction` (AI Risk Prediction panel: gauge, factors, 24h trend).

---

## 1. Setup

**Files needed in the same directory:**
- `ai_prediction_service.py` — the module
- `model2_weighted.joblib` — the trained model bundle (Model 2: Dynamic Rainfall-Triggered Landslide Risk)

**Dependencies:**
```bash
pip install numpy pandas xgboost shap joblib
```

**Import:**
```python
from ai_prediction_service import get_ai_prediction
```

---

## 2. Quick Start

```python
zones = [
    {
        "zone_id": "zone-aizawl",
        "district": "Aizawl",
        "state": "Mizoram",
        "features": {
            "susceptibility_score": 0.78,
            "slope_angle_deg": 38,
            "soil_type": "Silty Clay",
            "disturbance_index": 0.85,
            "rain_1d": 90, "rain_3d": 180, "rain_7d": 220,
            "rain_15d": 260, "rain_30d": 340, "api_index": 210,
            "seasonal_cum_rain": 500, "seasonal_rain_anomaly": 0.35,
            "soil_moisture": 0.86, "soil_moisture_trend": 0.22,
            "ndvi": 0.45, "ndvi_change_30d": -0.05,
        },
        "history": None,   # optional — see Section 5
    },
    # ... one dict per zone
]

result = get_ai_prediction(zones, district="Aizawl")
```

**Function signature:**
```python
get_ai_prediction(zones, zone_id=None, district=None) -> dict
```

| Argument | Type | Notes |
|---|---|---|
| `zones` | `list[dict]` | All candidate zones (see schema below) |
| `zone_id` | `str`, optional | Filter to one zone by ID |
| `district` | `str`, optional | Filter to one zone by district name (case-insensitive) |

If neither `zone_id` nor `district` is given, the function scores every zone in `zones` and returns the **highest-risk zone** — matching the API spec's default behavior.

Raises `ValueError` if no zone matches the given filter.

---

## 3. Input: the `features` dict (per zone)

This is the model's input — one snapshot of conditions for a zone at a point in time. All 15 fields below are used; the model tolerates missing values (pass `None` or omit the key) via graceful degradation, but include as many as you have for best accuracy.

### Static features (from Model 1 / GIS layers — don't change day to day)

| Feature | Type | Range | What it is |
|---|---|---|---|
| `susceptibility_score` | float | 0–1 | Model 1's output — structural landslide susceptibility of this zone (terrain, geology, historical activity) |
| `slope_angle_deg` | float | 0–90 | Terrain steepness in degrees |
| `soil_type` | string | one of: `"Clay"`, `"Silty Clay"`, `"Loam"`, `"Sandy Loam"`, `"Gravelly"` | Soil texture classification |
| `disturbance_index` | float | 0–1 | Human disturbance proxy — road cutting, quarrying, unplanned construction near the slope (Wayanad-type risk factor) |

### Dynamic features — rainfall

| Feature | Type | Units | What it is |
|---|---|---|---|
| `rain_1d` | float | mm | Rainfall in the last 1 day |
| `rain_3d` | float | mm | Cumulative rainfall, last 3 days |
| `rain_7d` | float | mm | Cumulative rainfall, last 7 days |
| `rain_15d` | float | mm | Cumulative rainfall, last 15 days |
| `rain_30d` | float | mm | Cumulative rainfall, last 30 days |
| `api_index` | float | mm (decay-weighted) | Antecedent Precipitation Index — decayed weighted sum of rainfall history (recent rain weighted more, older rain still counts) |
| `seasonal_cum_rain` | float | mm | Running total rainfall since the start of the current year for this zone |
| `seasonal_rain_anomaly` | float | ratio | (This season's rainfall so far − historical seasonal average) ÷ historical average. Positive = wetter than normal season |

### Dynamic features — soil condition

| Feature | Type | Range | What it is |
|---|---|---|---|
| `soil_moisture` | float | 0–1 | Current soil saturation level |
| `soil_moisture_trend` | float | typically -0.3 to 0.3 | Change in soil moisture over the past 3 days (rising = more dangerous) |

### Dynamic features — satellite/vegetation

| Feature | Type | Range | What it is |
|---|---|---|---|
| `ndvi` | float | 0–1 | Vegetation greenness index (current) |
| `ndvi_change_30d` | float | typically -0.4 to 0.4 | Change in NDVI over past 30 days. Negative = vegetation loss (disturbance signal) |

---

## 4. Zone dict — full schema

```python
{
    "zone_id": str,          # unique identifier, e.g. "zone-aizawl"
    "district": str,         # e.g. "Aizawl"
    "state": str,            # e.g. "Mizoram"
    "features": {...},       # current snapshot, schema above
    "history": [...] | None, # optional — 24h trend data, see Section 5
}
```

---

## 5. The `history` field (optional — for the 24h trend)

The model was trained on **daily** data, not sub-daily. The `trend` output needs 13 points at 2-hour steps across the last 24 hours. Two modes:

**A. Real data (preferred, once available):**
```python
"history": [
    {"time": "22:00", "features": {...same 15-field schema...}},
    {"time": "20:00", "features": {...}},
    ...  # 13 points, most recent LAST, covering the last 24h
]
```
Requires your backend to log a features snapshot per zone every 2 hours.

**B. No history supplied (`None` or omitted):**
The module **auto-simulates** a plausible 24h ramp by scaling the dynamic features down further into the past (storm-intensifying pattern), keeping static features constant. This lets the endpoint work immediately without a live 2-hourly logging pipeline.

**Either way, check the response's `trend_source` field** (`"real"` or `"simulated"`) to know which mode was used — see Section 6.

---

## 6. Output schema

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
    { "time": "03:52", "risk": 16 },
    { "time": "05:52", "risk": 16 },
    { "time": "07:52", "risk": 17 },
    { "time": "...", "risk": "..." },
    { "time": "03:52", "risk": 87 }
  ],
  "trend_source": "simulated"
}
```

| Field | Type | How it's produced |
|---|---|---|
| `district`, `state` | string | Passed through from the selected zone dict |
| `riskScore` | int, 0–100 | `round(fused_score × 100)` — the model's blended confidence |
| `status` | enum | Bucketed from `riskScore`: ≥80 `CRITICAL`, ≥60 `HIGH`, ≥35 `MODERATE`, else `LOW` |
| `summary` | string | Templated from `status` |
| `predictionWindow` | string | Templated from `status` (`CRITICAL`→6–12h, `HIGH`→12–24h, `MODERATE`→24–48h, `LOW`→48–72h) |
| `factors[].name` | string | One of the 5 fixed factor names (see below) |
| `factors[].level` | string | Human-readable bucket (`"Low"`/`"Moderate"`/`"High"`/`"Very High"`, or literal degrees for Slope) |
| `factors[].weight` | float, 0–1 | **Real SHAP value** for that feature group, aggregated from the trained XGBoost model and passed through a sigmoid — genuine per-instance feature attribution, not a static importance table |
| `trend[]` | array | 13 points, 2-hour steps, each re-scored through the model |
| `trend_source` | `"real"` \| `"simulated"` | Whether `trend[]` came from real supplied `history` or the auto-simulated fallback. **Not in the original API spec — extra field for debugging/data-quality visibility; strip it before final demo if the frontend doesn't expect it** |

### How each `factors[]` entry maps to underlying model features

| Factor name | Underlying features |
|---|---|
| Heavy Rainfall | `rain_15d`, `rain_30d`, `api_index`, `rain_7d`, `rain_3d`, `rain_1d`, `seasonal_cum_rain`, `seasonal_rain_anomaly` |
| Soil Moisture | `soil_moisture`, `soil_moisture_trend` |
| Slope | `slope_angle_deg` |
| Historical Activity | `susceptibility_score` |
| Terrain Stability | `disturbance_index`, `ndvi`, `ndvi_change_30d`, `soil_type` |

---

## 7. Internal helper (advanced use)

If you only need the raw model scores without the full API-shaped response:

```python
from ai_prediction_service import score_snapshot

xgb_probability, composite_score, fused_score = score_snapshot(features)
```

| Return value | Range | What it is |
|---|---|---|
| `xgb_probability` | 0–1 | Pure XGBoost model output |
| `composite_score` | 0–1 | Transparent rule-based weighted score (degrades gracefully with missing features) |
| `fused_score` | 0–1 | `alpha × xgb_probability + (1 − alpha) × composite_score` — this is what `riskScore` is derived from |

---

## 8. Known limitations (be upfront about these if asked)

- Model is trained on **synthetic/mock data** calibrated to realistic NER conditions — swap in real IMD/SMAP/Sentinel-2/GSI data before production use.
- `soil_moisture` and `soil_moisture_trend` currently rely on satellite proxies (e.g. SMAP) rather than ground sensors, since ground sensor coverage in remote NER zones is sparse.
- Probability calibration (`xgb_probability`) can vary somewhat between training runs due to the small number of positive (landslide) examples in the training data — the model's *ranking* of risk is reliable, exact decimal values less so until trained on more real historical events.
- `trend_source: "simulated"` responses are illustrative ramps, not measured sub-daily data — flag this clearly in any UI that displays them.