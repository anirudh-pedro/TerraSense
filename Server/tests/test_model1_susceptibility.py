"""Smoke/unit tests for Model 1 susceptibility inference.

Proves: 7 raw features -> 13 processed features -> successful XGBoost inference,
using the preprocessing reconstructed (and verified) from the training notebook.
"""

import numpy as np
import pytest

from app.services.ai import model1_susceptibility_service as m1

# A known real training row (notebook cell 52, true label = Landslide).
KNOWN_SAMPLE = dict(
    elevation=1367,
    slope=6.240689,
    aspect=261.487122,
    curvature=-15,
    ndvi=0.146611,
    lulc=60,
    rainfall=1929.161141,
)
# Susceptibility reproduced bit-for-bit from the notebook pipeline.
EXPECTED_SCORE = 0.898238


def test_processed_feature_order_is_13():
    assert len(m1.PROCESSED_FEATURE_ORDER) == 13
    assert m1.PROCESSED_FEATURE_ORDER[:6] == (
        "numeric__elevation", "numeric__slope", "numeric__aspect",
        "numeric__curvature", "numeric__ndvi", "numeric__rainfall",
    )
    assert m1.PROCESSED_FEATURE_ORDER[6:] == tuple(f"lulc__lulc_{c}" for c in (10, 30, 40, 50, 60, 80, 90))


def test_preprocess_produces_13_features():
    X = m1.build_feature_vector(**KNOWN_SAMPLE)
    assert X.shape == (1, 13)
    # LULC=60 -> the 5th one-hot slot (index 6+4=10) is hot, rest zero
    assert X[0, 6:].sum() == 1.0
    assert X[0, 10] == 1.0


def test_known_sample_inference_matches_notebook():
    result = m1.predict_susceptibility(**KNOWN_SAMPLE)
    assert 0.0 <= result["susceptibility_score"] <= 1.0
    assert abs(result["susceptibility_score"] - EXPECTED_SCORE) < 1e-3
    assert result["classification"] == "Very High"
    assert result["model_version"] == "1.0"
    assert result["model_name"]
    assert set(result["features_used"]) == set(m1.RAW_FEATURES)


def test_unknown_lulc_maps_to_all_zero_onehot():
    X = m1.build_feature_vector(**{**KNOWN_SAMPLE, "lulc": 70})  # 70 not in learned categories
    assert X[0, 6:].sum() == 0.0
    # Still scores without a feature-count error.
    result = m1.predict_susceptibility(**{**KNOWN_SAMPLE, "lulc": 70})
    assert 0.0 <= result["susceptibility_score"] <= 1.0


def test_missing_numeric_feature_raises():
    with pytest.raises(ValueError):
        m1.predict_susceptibility(
            elevation=None, slope=6, aspect=100, curvature=0, ndvi=0.4, lulc=10, rainfall=2000
        )


def test_matches_manual_reference_vector():
    """Independent manual construction of the 13-vector must equal the service's."""
    s = KNOWN_SAMPLE
    manual = [s["elevation"], s["slope"], s["aspect"], s["curvature"], s["ndvi"], s["rainfall"]]
    manual += [1.0 if 60 == c else 0.0 for c in (10, 30, 40, 50, 60, 80, 90)]
    assert np.allclose(m1.build_feature_vector(**s)[0], np.array(manual, dtype=float))
