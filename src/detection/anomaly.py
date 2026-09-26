"""
Geo Regreen Detection Engine - Anomaly
Engine: GeoRegreen Engine 0.1.0

Purpose:
    Compare current observation vs seasonal baseline.
    Outputs are fully explainable and reproducible for
    mining / water / insurance audits.

Defensibility spec:
    AOI, Data, Period, Baseline, Cloud/Quality, Index,
    Current, Baseline_val, Anomaly, Persistence,
    Threshold Config, Processing Version, Generated

Outputs:
    Bands: current, baseline, absolute_anomaly, pct_anomaly, z_score (optional)
    Properties: full provenance
"""

from __future__ import annotations

import ee
from typing import Dict, Any, Optional

# Engine constants - single source of truth
PROCESSING_VERSION = "GeoRegreen Engine 0.1.0"
DEFAULT_EPSILON = 1e-6

# Band names - frozen for downstream pipeline
BAND_CURRENT = "current"
BAND_BASELINE = "baseline"
BAND_ABS_ANOMALY = "absolute_anomaly"
BAND_PCT_ANOMALY = "pct_anomaly"
BAND_Z_SCORE = "z_score"

def calculate_anomaly(
    current: ee.Image,
    baseline: ee.Image,
    baseline_std: Optional[ee.Image] = None,
    epsilon: float = DEFAULT_EPSILON,
    provenance: Optional[Dict[str, Any]] = None,
) -> ee.Image:
    """
    Calculate defensible environmental anomaly.

    provenance dict must contain (for audit):
        aoi_id, data_source, period, baseline_period,
        cloud_method, index, threshold_config
    """
    current = ee.Image(current).toFloat()
    baseline = ee.Image(baseline).toFloat()

    # ---------------------------------------------------------
    # 1. Absolute anomaly: current - baseline
    # ---------------------------------------------------------
    absolute_anomaly = (
        current.subtract(baseline)
        .rename(BAND_ABS_ANOMALY)
    )

    # ---------------------------------------------------------
    # 2. Percentage anomaly: (current-baseline)/|baseline| * 100
    #    Neutralizes Zero-Denominator Trap
    # ---------------------------------------------------------
    denominator = baseline.abs().max(ee.Image.constant(epsilon))
    
    pct_anomaly = (
        current.subtract(baseline)
        .divide(denominator)
        .multiply(100)
        .rename(BAND_PCT_ANOMALY)
    )
    
    # Mask where baseline is effectively zero -> pct meaningless
    pct_anomaly = pct_anomaly.updateMask(
        baseline.abs().gte(epsilon)
    )

    # ---------------------------------------------------------
    # 3. Z-score: (current-baseline)/std
    #    Neutralizes Zero-Variance Trap
    # ---------------------------------------------------------
    bands = [
        current.rename(BAND_CURRENT),
        baseline.rename(BAND_BASELINE),
        absolute_anomaly,
        pct_anomaly
    ]

    if baseline_std is not None:
        baseline_std = ee.Image(baseline_std).toFloat()
        safe_std = baseline_std.max(ee.Image.constant(epsilon))
        
        z_score = (
            current.subtract(baseline)
            .divide(safe_std)
            .rename(BAND_Z_SCORE)
        ).updateMask(baseline_std.gte(epsilon))
        
        bands.append(z_score)

    result = ee.Image.cat(bands)

    # ---------------------------------------------------------
    # 4. PROVENANCE - This is defensibility
    # ---------------------------------------------------------
    prov = provenance or {}
    result = result.setMulti({
        "processing_version": PROCESSING_VERSION,
        "aoi_id": prov.get("aoi_id", "unknown"),
        "data_source": prov.get("data_source", "Sentinel-2"),
        "period": prov.get("period", "unknown"),
        "baseline_period": prov.get("baseline_period", "unknown"),
        "cloud_method": prov.get("cloud_method", "unknown"),
        "index": prov.get("index", "unknown"),
        "threshold_config": prov.get("threshold_config", "agriculture_v1"),
        "epsilon": epsilon,
        "generated_utc": ee.Date(ee.Date.now()).format("YYYY-MM-dd'T'HH:mm:ss'Z'"),
        "engine": "anomaly"
    })

    return result

def extract_anomaly_telemetry(
    anomaly_image: ee.Image,
    aoi: ee.Geometry,
    scale: int = 10,
) -> Dict[str, Any]:
    """
    AOI-Level Summary Extractor
    Turns raster anomalies into the exact telemetry record your mentor wants.
    
    Returns dict for one farm/dam:
        {
          current: 0.42,
          baseline: 0.60,
          absolute_anomaly: -0.18,
          pct_anomaly: -30.0,
          z_score: -2.1
        }
    + provenance from image properties
    """
    # Mean over AOI - defensible aggregation
    stats = anomaly_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=aoi,
        scale=scale,
        maxPixels=1e9
    )

    # Pull provenance from image properties
    prov = anomaly_image.toDictionary([
        "aoi_id", "data_source", "period", "baseline_period",
        "cloud_method", "index", "threshold_config",
        "processing_version", "generated_utc"
    ])

    return {
        "telemetry": stats,
        "provenance": prov
    }