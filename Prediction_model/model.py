"""
ai_prediction_service.py
--------------------------
Importable module implementing the GET /ai/prediction contract for the
AI Risk Prediction panel (gauge + factors + 24h trend).

Usage (for your teammate):

    from ai_prediction_service import get_ai_prediction

    zones = [
        {
            "zone_id": "zone-aizawl",
            "district": "Aizawl",
            "state": "Mizoram",
            "features": {          # current snapshot, same schema as training data
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
            "history": None,        # optional -- see below
        },
        # ... more zones
    ]

    result = get_ai_prediction(zones, district="Aizawl")
    # -> dict matching the exact API response schema

If "history" is omitted (None), a plausible 24h ramp is auto-simulated
from the current snapshot (clearly flagged in the response via
"trend_source": "simulated"). If you DO have real 2-hourly sensor/
rainfall history, pass it as:

    "history": [
        {"time": "22:00", "features": {...same schema as above...}},
        {"time": "20:00", "features": {...}},
        ...  # up to 13 points covering the last 24h, most recent LAST
    ]

and the real values will be scored instead (response will say
"trend_source": "real").
"""

import math
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import xgboost as xgb
import shap
import joblib

MODEL_PATH = "model2_weighted.joblib"

# =================================================================
# Model bundle -- loaded once, cached at module level
# =================================================================
_bundle = None
_explainer = None


def _load():
    global _bundle, _explainer
    if _bundle is None:
        _bundle = joblib.load(MODEL_PATH)
        _explainer = shap.TreeExplainer(_bundle["xgb_model"])
    return _bundle, _explainer


# =================================================================
# Category -> raw column mapping (rebuilds the same weighting scheme
# used in training; also used here to aggregate SHAP values into the
# 5 human-facing factors the API expects)
# =================================================================
FACTOR_CATEGORY_COLUMNS = {
    "rainfall": ["api_index", "rain_15d", "rain_30d", "rain_7d", "rain_3d", "rain_1d",
                 "seasonal_cum_rain", "seasonal_rain_anomaly"],
    "soil_moisture": ["soil_moisture", "soil_moisture_trend"],
    "slope": ["slope_angle_deg"],
    "susceptibility": ["susceptibility_score"],
    "terrain_stability": ["disturbance_index", "ndvi", "ndvi_change_30d"],  # + soiltype dummies added at runtime
}

STATIC_FEATURES = {"susceptibility_score", "slope_angle_deg", "soil_type", "disturbance_index"}
DYNAMIC_FEATURES = [
    "rain_1d", "rain_3d", "rain_7d", "rain_15d", "rain_30d", "api_index",
    "seasonal_cum_rain", "seasonal_rain_anomaly", "soil_moisture",
    "soil_moisture_trend", "ndvi", "ndvi_change_30d",
]

STATUS_THRESHOLDS = [(80, "CRITICAL"), (60, "HIGH"), (35, "MODERATE"), (0, "LOW")]
PREDICTION_WINDOW = {
    "CRITICAL": "Next 6–12 hours",
    "HIGH": "Next 12–24 hours",
    "MODERATE": "Next 24–48 hours",
    "LOW": "Next 48–72 hours",
}
SUMMARY_TEMPLATE = {
    "CRITICAL": "High probability of slope failure within the {window}.",
    "HIGH": "Elevated probability of slope failure within the {window}.",
    "MODERATE": "Moderate risk conditions developing within the {window}.",
    "LOW": "Conditions currently stable; low landslide risk over the {window}.",
}


# =================================================================
# Core scoring (mirrors train_model2_weighted.py logic exactly)
# =================================================================
def _minmax(val, lo, hi):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return np.nan
    return float(np.clip((val - lo) / (hi - lo), 0, 1))


def _composite_score(features, category_weights, norm_bounds, soil_type_risk):
    signals = {}
    rain_vals = [
        _minmax(features.get("api_index"), *norm_bounds["api_index"]),
        _minmax(features.get("rain_15d"), *norm_bounds["rain_15d"]),
        _minmax(features.get("rain_30d"), *norm_bounds["rain_30d"]),
    ]
    rain_vals = [v for v in rain_vals if not pd.isna(v)]
    signals["rainfall"] = np.mean(rain_vals) if rain_vals else np.nan

    sm = _minmax(features.get("soil_moisture"), *norm_bounds["soil_moisture"])
    trend = features.get("soil_moisture_trend")
    trend_signal = _minmax(max(trend, 0) if trend is not None else None,
                            *norm_bounds["soil_moisture_trend"])
    soil_vals = [v for v in [sm, trend_signal] if not pd.isna(v)]
    signals["soil_moisture"] = np.mean(soil_vals) if soil_vals else np.nan

    signals["susceptibility"] = features.get("susceptibility_score", np.nan)
    signals["disturbance"] = features.get("disturbance_index", np.nan)

    anomaly = features.get("seasonal_rain_anomaly")
    signals["seasonal_anomaly"] = _minmax(
        max(anomaly, 0) if anomaly is not None else None, *norm_bounds["seasonal_rain_anomaly"])

    slope = features.get("slope_angle_deg")
    slope_signal = _minmax(slope, 0, 60) if slope is not None else np.nan
    soil_type_signal = soil_type_risk.get(features.get("soil_type"), np.nan)
    ts_vals = [v for v in [slope_signal, soil_type_signal] if not pd.isna(v)]
    signals["terrain_soil_static"] = np.mean(ts_vals) if ts_vals else np.nan

    ndvi_change = features.get("ndvi_change_30d")
    signals["vegetation"] = (
        float(np.clip(abs(min(ndvi_change, 0)) / 0.3, 0, 1)) if ndvi_change is not None else np.nan
    )

    available = {k: v for k, v in signals.items() if not pd.isna(v)}
    if not available:
        return 0.0
    weight_sum = sum(category_weights[k] for k in available)
    return round(sum(category_weights[k] * v for k, v in available.items()) / weight_sum, 4)


def _to_model_row(features, all_features):
    """Build a single-row DataFrame matching the model's expected columns."""
    row = {c: features.get(c, np.nan) for c in all_features if not c.startswith("soiltype_")}
    df = pd.DataFrame([row])
    soil_type = features.get("soil_type")
    for c in all_features:
        if c.startswith("soiltype_"):
            df[c] = 1 if c == f"soiltype_{soil_type}" else 0
    return df[all_features]


def score_snapshot(features):
    """Score one feature snapshot -> (xgb_probability, composite_score, fused_score)."""
    bundle, _ = _load()
    all_features = bundle["features"]
    X = _to_model_row(features, all_features)
    dmat = xgb.DMatrix(X, feature_names=all_features, missing=np.nan)
    xgb_prob = float(bundle["xgb_model"].predict(dmat)[0])
    composite = _composite_score(
        features, bundle["category_weights"], bundle["norm_bounds"], bundle["soil_type_risk"])
    fused = bundle["alpha"] * xgb_prob + (1 - bundle["alpha"]) * composite
    return xgb_prob, composite, float(fused)


def _status_from_score(risk_score):
    for threshold, label in STATUS_THRESHOLDS:
        if risk_score >= threshold:
            return label
    return "LOW"


# =================================================================
# Factor levels (human-readable labels per factor)
# =================================================================
def _bucket(value, edges, labels):
    for edge, label in zip(edges, labels):
        if value < edge:
            return label
    return labels[-1]


def _factor_levels(features):
    rain_15d = features.get("rain_15d", 0)
    soil_moisture = features.get("soil_moisture", 0)
    susceptibility = features.get("susceptibility_score", 0)
    disturbance = features.get("disturbance_index", 0)

    SOIL_TYPE_RISK = _load()[0]["soil_type_risk"]
    soil_type_risk = SOIL_TYPE_RISK.get(features.get("soil_type"), 0.5)
    stability_score = 1 - (0.6 * disturbance + 0.4 * soil_type_risk)  # higher = more stable

    return {
        "Heavy Rainfall": _bucket(rain_15d, [60, 150, 300], ["Low", "Moderate", "High", "Very High"]),
        "Soil Moisture": _bucket(soil_moisture, [0.4, 0.6, 0.8], ["Low", "Moderate", "High", "Very High"]),
        "Slope": f"{features.get('slope_angle_deg', 0):.0f}°",
        "Historical Activity": _bucket(susceptibility, [0.3, 0.5, 0.7], ["Low", "Moderate", "High", "Very High"]),
        "Terrain Stability": _bucket(stability_score, [0.3, 0.6], ["Low", "Moderate", "High"]),
    }


def _factor_weights_from_shap(features):
    """SHAP-based per-factor weight (0-1), aggregated from raw feature
    contributions into the 5 named categories."""
    bundle, explainer = _load()
    all_features = bundle["features"]
    X = _to_model_row(features, all_features)
    shap_values = explainer.shap_values(X)[0]  # log-odds contribution per raw feature
    shap_by_col = dict(zip(all_features, shap_values))

    soiltype_cols = [c for c in all_features if c.startswith("soiltype_")]

    def category_weight(cols):
        contribution = sum(shap_by_col.get(c, 0.0) for c in cols)
        weight = 1 / (1 + math.exp(-contribution))  # sigmoid -> 0-1 intensity
        return round(float(np.clip(weight, 0.02, 0.99)), 2)

    return {
        "Heavy Rainfall": category_weight(FACTOR_CATEGORY_COLUMNS["rainfall"]),
        "Soil Moisture": category_weight(FACTOR_CATEGORY_COLUMNS["soil_moisture"]),
        "Slope": category_weight(FACTOR_CATEGORY_COLUMNS["slope"]),
        "Historical Activity": category_weight(FACTOR_CATEGORY_COLUMNS["susceptibility"]),
        "Terrain Stability": category_weight(FACTOR_CATEGORY_COLUMNS["terrain_stability"] + soiltype_cols),
    }


def _build_factors(features):
    levels = _factor_levels(features)
    weights = _factor_weights_from_shap(features)
    return [
        {"name": name, "level": levels[name], "weight": weights[name]}
        for name in ["Heavy Rainfall", "Soil Moisture", "Slope", "Historical Activity", "Terrain Stability"]
    ]


# =================================================================
# 24h trend (real history if supplied, else simulated ramp fallback)
# =================================================================
def _simulate_history(current_features, now=None, num_points=13, step_hours=2):
    """Fallback: interpolate a plausible 24h ramp ending at current
    conditions. Static features stay constant; dynamic (rainfall/soil/
    NDVI) features are scaled down further into the past using a smooth
    ease-in curve, mimicking a strengthening storm building toward now.
    This is a SIMULATED fallback -- replace with real 2-hourly sensor/
    rainfall history as soon as that pipeline exists.
    """
    now = now or datetime.now()
    points = []
    for i in range(num_points):
        hours_ago = (num_points - 1 - i) * step_hours
        t = now - timedelta(hours=hours_ago)
        # ease-in ramp: 0.35 at -24h -> 1.0 at now (quadratic ease-in)
        progress = 1 - (hours_ago / ((num_points - 1) * step_hours)) if num_points > 1 else 1
        scale = 0.35 + 0.65 * (progress ** 2)
        snap = dict(current_features)
        for f in DYNAMIC_FEATURES:
            if f in snap and snap[f] is not None:
                snap[f] = snap[f] * scale
        points.append({"time": t.strftime("%H:%M"), "features": snap})
    return points


def _build_trend(current_features, history=None):
    if history:
        points = history
        source = "real"
    else:
        points = _simulate_history(current_features)
        source = "simulated"

    trend = []
    for point in points:
        _, _, fused = score_snapshot(point["features"])
        trend.append({"time": point["time"], "risk": round(fused * 100)})
    return trend, source


# =================================================================
# Public API: get_ai_prediction
# =================================================================
def get_ai_prediction(zones, zone_id=None, district=None):
    """
    zones: list of dicts, each:
        {
            "zone_id": str, "district": str, "state": str,
            "features": {...current snapshot...},
            "history": [{"time": "HH:MM", "features": {...}}, ...] or None
        }
    zone_id / district: optional filters. If neither given, the
    highest-risk zone (by fused_score) among `zones` is used.

    Returns a dict matching the GET /ai/prediction response schema.
    """
    if zone_id:
        matches = [z for z in zones if z.get("zone_id") == zone_id]
    elif district:
        matches = [z for z in zones if z.get("district", "").lower() == district.lower()]
    else:
        matches = zones

    if not matches:
        raise ValueError(f"No zone found for zone_id={zone_id!r} district={district!r}")

    scored = []
    for z in matches:
        _, _, fused = score_snapshot(z["features"])
        scored.append((fused, z))
    scored.sort(key=lambda x: x[0], reverse=True)
    fused_score, zone = scored[0]

    risk_score = round(fused_score * 100)
    status = _status_from_score(risk_score)
    prediction_window = PREDICTION_WINDOW[status]
    summary = SUMMARY_TEMPLATE[status].format(window=prediction_window.lower())

    factors = _build_factors(zone["features"])
    trend, trend_source = _build_trend(zone["features"], zone.get("history"))

    return {
        "district": zone.get("district"),
        "state": zone.get("state"),
        "riskScore": risk_score,
        "status": status,
        "summary": summary,
        "predictionWindow": prediction_window,
        "factors": factors,
        "trend": trend,
        "trend_source": trend_source,  # extra field: "real" or "simulated" -- lets frontend/backend know data quality
    }


# =================================================================
# Demo / smoke test
# =================================================================
if __name__ == "__main__":
    import json

    demo_zones = [
        {
            "zone_id": "zone-aizawl",
            "district": "Aizawl",
            "state": "Mizoram",
            "features": {
                "susceptibility_score": 0.78, "slope_angle_deg": 38,
                "soil_type": "Silty Clay", "disturbance_index": 0.85,
                "rain_1d": 90, "rain_3d": 180, "rain_7d": 220,
                "rain_15d": 260, "rain_30d": 340, "api_index": 210,
                "seasonal_cum_rain": 500, "seasonal_rain_anomaly": 0.35,
                "soil_moisture": 0.86, "soil_moisture_trend": 0.22,
                "ndvi": 0.45, "ndvi_change_30d": -0.05,
            },
            "history": None,  # will auto-simulate
        },
        {
            "zone_id": "zone-champhai",
            "district": "Champhai",
            "state": "Mizoram",
            "features": {
                "susceptibility_score": 0.35, "slope_angle_deg": 20,
                "soil_type": "Sandy Loam", "disturbance_index": 0.15,
                "rain_1d": 5, "rain_3d": 10, "rain_7d": 20,
                "rain_15d": 30, "rain_30d": 50, "api_index": 15,
                "seasonal_cum_rain": 100, "seasonal_rain_anomaly": -0.2,
                "soil_moisture": 0.35, "soil_moisture_trend": 0.0,
                "ndvi": 0.6, "ndvi_change_30d": 0.0,
            },
            "history": None,
        },
    ]

    print("=== Query by district=Aizawl ===")
    print(json.dumps(get_ai_prediction(demo_zones, district="Aizawl"), indent=2))

    print("\n=== Query with no filter (defaults to highest-risk zone) ===")
    print(json.dumps(get_ai_prediction(demo_zones), indent=2))