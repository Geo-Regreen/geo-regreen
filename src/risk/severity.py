"""
Geo Regreen Risk Engine - Severity
Engine: GeoRegreen Engine 0.1.0

Purpose:
    Turn magnitude + persistence into 0-100 + Low/Med/High/Critical

What it answers:
    How bad? 72/100 High Severity

Scoring:
    severity = 60% magnitude + 25% persistence + 15% change_severity
"""

from __future__ import annotations
import ee
from typing import Dict, Optional

PROCESSING_VERSION = "GeoRegreen Engine 0.1.0"

BAND_SEV_SCORE = "severity_score"
BAND_SEV_LEVEL = "severity_level"  # 1=Low, 2=Medium, 3=High, 4=Critical
BAND_MAG_SCORE = "magnitude_score"

# Versioned scoring models - AUDIT LAYER
SEVERITY_MODELS: Dict[str, Dict[str, float]] = {
    "default_v1": {"w_mag": 0.60, "w_pers": 0.25, "w_change": 0.15, "z_cap": 3.0, "abs_cap": 0.30, "pers_cap": 6.0},
    "agriculture_v1": {"w_mag": 0.60, "w_pers": 0.25, "w_change": 0.15, "z_cap": 3.0, "abs_cap": 0.30, "pers_cap": 6.0},
    "mining_v1": {"w_mag": 0.50, "w_pers": 0.35, "w_change": 0.15, "z_cap": 2.5, "abs_cap": 0.25, "pers_cap": 4.0},
}

def calculate_severity(
    anomaly_image: ee.Image,
    persistence_image: Optional[ee.Image] = None,
    model_name: str = "default_v1",
) -> ee.Image:
    """
    Premium severity: direction-aware + multi-criteria + level.
    """
    cfg = SEVERITY_MODELS.get(model_name, SEVERITY_MODELS["default_v1"])
    
    base = ee.Image(anomaly_image)

    # --- PREMIUM FIX 1: Server-safe band selection ---
    has_z = base.bandNames().contains("z_score")
    has_abs = base.bandNames().contains("absolute_anomaly")
    has_change_sev = base.bandNames().contains("change_severity")

    # magnitude = |z| / cap if exists, else |abs| / cap
    z_score = ee.Image(ee.Algorithms.If(has_z, base.select("z_score"), ee.Image.constant(0)))
    abs_anom = ee.Image(ee.Algorithms.If(has_abs, base.select("absolute_anomaly"), z_score))

    mag_value = ee.Image(ee.Algorithms.If(has_z, z_score.abs(), abs_anom.abs()))
    mag_cap = ee.Image(ee.Algorithms.If(has_z, ee.Image.constant(cfg["z_cap"]), ee.Image.constant(cfg["abs_cap"])))

    mag_score = mag_value.divide(mag_cap).min(1).multiply(100).rename(BAND_MAG_SCORE)

    # --- PREMIUM FIX 2: Persistence + Change Severity ---
    pers_score = ee.Image.constant(0)
    if persistence_image is not None:
        p_img = ee.Image(persistence_image)
        has_pers_count = p_img.bandNames().contains("persistence_count")
        # Use deg count if available for degradation-aware scoring
        count_band = ee.Algorithms.If(has_pers_count, p_img.select("persistence_count"), p_img.select(0))
        count_band = ee.Image(count_band)
        pers_score = count_band.divide(cfg["pers_cap"]).min(1).multiply(100)

    change_sev_score = ee.Image(ee.Algorithms.If(
        has_change_sev,
        base.select("change_severity").divide(2).multiply(100),  # 0,1,2 -> 0,50,100
        ee.Image.constant(0)
    ))
    change_sev_score = ee.Image(change_sev_score)

    # Weighted blend
    severity = (
        mag_score.multiply(cfg["w_mag"])
        .add(pers_score.multiply(cfg["w_pers"]))
        .add(change_sev_score.multiply(cfg["w_change"]))
    )

    severity_score = severity.clamp(0, 100).rename(BAND_SEV_SCORE)

    # --- PREMIUM FIX 3: Severity LEVEL for boardroom ---
    # 1=Low <30, 2=Medium 30-60, 3=High 60-85, 4=Critical >85
    severity_level = (
        ee.Image.constant(1)
        .where(severity_score.gte(30), 2)
        .where(severity_score.gte(60), 3)
        .where(severity_score.gte(85), 4)
        .rename(BAND_SEV_LEVEL)
    )

    result = base.addBands([mag_score, severity_score, severity_level])
    
    return result.set({
        "processing_version": PROCESSING_VERSION,
        "engine": "severity",
        "engine_chain": "anomaly->change->persistence->severity",
        "severity_model": model_name,
        "w_magnitude": cfg["w_mag"],
        "w_persistence": cfg["w_pers"],
        "w_change_severity": cfg["w_change"],
        "severity_tiers": "{1:Low <30, 2:Medium 30-60, 3:High 60-85, 4:Critical >85}",
        "scoring_note": "Calibrate against historical events before presenting as validated risk"
    })

def extract_severity_telemetry(image: ee.Image, aoi: ee.Geometry, scale: int = 10):
    return image.select([BAND_SEV_SCORE, BAND_SEV_LEVEL, BAND_MAG_SCORE]).reduceRegion(
        ee.Reducer.mean(), geometry=aoi, scale=scale, maxPixels=1e9
    )