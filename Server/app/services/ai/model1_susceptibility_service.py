"""Model 1 — NER Landslide Susceptibility inference service.

Reproduces the EXACT training-time preprocessing so raw 7 features can be scored
by the saved XGBoost classifier (which expects 13 processed features).

Why 7 -> 13 (root cause)
------------------------
The training notebook fit a scikit-learn ``ColumnTransformer``:
    * ``passthrough`` for 6 numeric features, in this order:
        elevation, slope, aspect, curvature, ndvi, rainfall
      (note: ``lulc`` is NOT numeric-passed, and rainfall is 6th)
    * ``OneHotEncoder(handle_unknown="ignore")`` on ``lulc``, which learned
      exactly 7 categories: [10, 30, 40, 50, 60, 80, 90]
The classifier was then ``.fit`` on the transformed array -> 6 + 7 = 13 columns.
The fitted transformer was **not** saved in the .joblib bundle (only the model +
metadata), so this module reconstructs the identical preprocessing. The exact
column order and LULC categories were recovered from the notebook's
``preprocessor.get_feature_names_out()`` output and verified to reproduce the
notebook's ``predict_proba`` results bit-for-bit.

LULC one-hot uses ``handle_unknown="ignore"`` semantics: any LULC value not in
the learned set (or missing) maps to an all-zero one-hot block — matching training.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np
import joblib

logger = logging.getLogger(__name__)

# Robust artifact path: env override, else the bundle shipped under app/ml/.
MODEL_PATH = os.environ.get("MODEL1_PATH") or str(
    Path(__file__).resolve().parents[2] / "ml" / "model1_landslide_susceptibility.joblib"
)

# --- Reconstructed training-time preprocessing (verified against the notebook) ---
NUMERIC_FEATURES: tuple[str, ...] = ("elevation", "slope", "aspect", "curvature", "ndvi", "rainfall")
LULC_CATEGORIES: tuple[int, ...] = (10, 30, 40, 50, 60, 80, 90)
PROCESSED_FEATURE_ORDER: tuple[str, ...] = (
    tuple(f"numeric__{c}" for c in NUMERIC_FEATURES)
    + tuple(f"lulc__lulc_{c}" for c in LULC_CATEGORIES)
)  # exactly 13, matching booster n_features_in_

RAW_FEATURES: tuple[str, ...] = ("elevation", "slope", "aspect", "curvature", "ndvi", "lulc", "rainfall")


class Model1Unavailable(Exception):
    """Raised when the Model 1 artifact/deps are unavailable or inconsistent."""


@lru_cache(maxsize=1)
def _bundle() -> dict:
    """Load and cache the Model 1 bundle."""
    try:
        bundle = joblib.load(MODEL_PATH)
    except FileNotFoundError as exc:
        raise Model1Unavailable(f"Model 1 artifact not found at {MODEL_PATH}") from exc
    logger.info(
        "Loaded Model 1 '%s' v%s (expects %d features)",
        bundle.get("model_name"), bundle.get("model_version"), bundle["model"].n_features_in_,
    )
    return bundle


def _num(name: str, value) -> float:
    if value is None:
        raise ValueError(f"'{name}' is required and cannot be None.")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"'{name}' must be numeric, got {value!r}.") from exc


def _lulc_onehot(lulc) -> list[float]:
    """One-hot the LULC value over the learned categories.

    Unknown/missing LULC -> all zeros (handle_unknown='ignore' behavior).
    """
    code: Optional[int]
    try:
        code = int(round(float(lulc))) if lulc is not None else None
    except (TypeError, ValueError):
        code = None
    if code is not None and code not in LULC_CATEGORIES:
        logger.debug("LULC %s not in learned categories %s -> all-zero one-hot", code, LULC_CATEGORIES)
    return [1.0 if code == cat else 0.0 for cat in LULC_CATEGORIES]


def build_feature_vector(elevation, slope, aspect, curvature, ndvi, lulc, rainfall) -> np.ndarray:
    """Turn the 7 raw features into the model's exact 13-column input (shape (1, 13))."""
    numeric = [
        _num("elevation", elevation),
        _num("slope", slope),
        _num("aspect", aspect),
        _num("curvature", curvature),
        _num("ndvi", ndvi),
        _num("rainfall", rainfall),
    ]
    vector = numeric + _lulc_onehot(lulc)
    return np.asarray([vector], dtype=float)


def _classify(score: float, thresholds: dict) -> str:
    """Map a 0-1 score to a class using the bundle's thresholds.

    thresholds e.g. {'Very Low':0.2,'Low':0.4,'Moderate':0.6,'High':0.8};
    scores >= the top edge are 'Very High'.
    """
    for label, edge in sorted(thresholds.items(), key=lambda kv: kv[1]):
        if score < edge:
            return label
    return "Very High"


def predict_susceptibility(elevation, slope, aspect, curvature, ndvi, lulc, rainfall) -> dict:
    """Predict landslide susceptibility for one location from the 7 raw features.

    Returns:
        {
            "susceptibility_score": float 0-1  (P(Landslide)),
            "classification": str,
            "model_name": str,
            "model_version": str,
            "features_used": {raw 7 inputs},
        }
    """
    bundle = _bundle()
    model = bundle["model"]

    X = build_feature_vector(elevation, slope, aspect, curvature, ndvi, lulc, rainfall)
    expected = int(model.n_features_in_)
    if X.shape[1] != expected:
        raise Model1Unavailable(
            f"Preprocessing produced {X.shape[1]} features but the model expects {expected}."
        )

    score = float(np.clip(model.predict_proba(X)[0, 1], 0.0, 1.0))
    classification = _classify(score, bundle["susceptibility_thresholds"])

    return {
        "susceptibility_score": round(score, 6),
        "classification": classification,
        "model_name": bundle["model_name"],
        "model_version": bundle["model_version"],
        "features_used": {
            "elevation": elevation,
            "slope": slope,
            "aspect": aspect,
            "curvature": curvature,
            "ndvi": ndvi,
            "lulc": lulc,
            "rainfall": rainfall,
        },
    }
