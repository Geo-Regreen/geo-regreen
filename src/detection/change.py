"""
Geo Regreen Detection Engine - Change
Engine: GeoRegreen Engine 0.1.0

Purpose:
    Translate anomaly math into defensible business change types.

    Answers: What changed? How severe?

Defensibility:
    Every pixel carries threshold_config + exact thresholds used.
"""

from __future__ import annotations
import ee
from typing import Dict

PROCESSING_VERSION = "GeoRegreen Engine 0.1.0"

# --- Frozen Constants ---
CHANGE_STABLE = 0
CHANGE_DEGRADATION = 1
CHANGE_RECOVERY = 2

# --- Versioned Threshold Registry - THE AUDIT LAYER ---
# Each sector has own physics + stats
SECTOR_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "agriculture_v1": {"abs_deg": -0.15, "abs_rec": 0.15, "z_deg": -1.5, "z_rec": 1.5, "severe_abs": -0.30},
    "water_v1":       {"abs_deg": -0.10, "abs_rec": 0.10, "z_deg": -1.2, "z_rec": 1.2, "severe_abs": -0.25},
    "mining_v1":      {"abs_deg": -0.08, "abs_rec": 0.08, "z_deg": -1.0, "z_rec": 1.0, "severe_abs": -0.20},
    "wetland_v1":     {"abs_deg": -0.12, "abs_rec": 0.12, "z_deg": -1.3, "z_rec": 1.3, "severe_abs": -0.28},
}

def classify_change(
    anomaly_image: ee.Image,
    config_name: str = "agriculture_v1",
) -> ee.Image:
    """
    Multi-criteria, severity-aware classification.
    
    Logic (Defensible):
      Degradation = absolute_anomaly < abs_deg AND z_score < z_deg
      This stops noise from triggering flags.

    Returns bands:
      change_type: 0=Stable, 1=Degradation, 2=Recovery
      change_severity: 0=none, 1=moderate, 2=severe
      change_confidence: proxy = |z_score|
    """
    cfg = SECTOR_THRESHOLDS.get(config_name)
    if cfg is None:
        raise ValueError(f"Unknown config {config_name}. Valid: {list(SECTOR_THRESHOLDS.keys())}")

    anomaly_image = ee.Image(anomaly_image)
    abs_anom = anomaly_image.select("absolute_anomaly")
    
    # --- ELITE FIX 1: Server-safe band existence check ---
    # Don't use Python if. Use EE logic.
    has_z = anomaly_image.bandNames().contains("z_score")
    z = ee.Image(ee.Algorithms.If(has_z, anomaly_image.select("z_score"), ee.Image.constant(0))).rename("z_score")
    
    # Degradation must breach BOTH physics and statistics if z exists
    cond_abs_deg = abs_anom.lte(cfg["abs_deg"])
    cond_z_deg = ee.Algorithms.If(has_z, z.lte(cfg["z_deg"]), ee.Image.constant(1))
    cond_z_deg = ee.Image(cond_z_deg)

    cond_abs_rec = abs_anom.gte(cfg["abs_rec"])
    cond_z_rec = ee.Algorithms.If(has_z, z.gte(cfg["z_rec"]), ee.Image.constant(1))
    cond_z_rec = ee.Image(cond_z_rec)

    degradation = cond_abs_deg.And(cond_z_deg)
    recovery = cond_abs_rec.And(cond_z_rec)

    # --- ELITE FIX 2: Severity Gradient ---
    # 0=stable, 1=moderate degradation, 2=severe degradation
    severity = (
        ee.Image.constant(0)
        .where(degradation, 1)
        .where(degradation.And(abs_anom.lte(cfg["severe_abs"])), 2)
        .rename("change_severity")
    )

    change_type = (
        ee.Image.constant(CHANGE_STABLE)
        .where(degradation, CHANGE_DEGRADATION)
        .where(recovery, CHANGE_RECOVERY)
        .rename("change_type")
    )

    # Confidence = |z| if available, else normalized |abs_anomaly|
    confidence = ee.Image(ee.Algorithms.If(
        has_z,
        z.abs().rename("change_confidence"),
        abs_anom.abs().divide(0.3).clamp(0, 3).rename("change_confidence")
    ))

    # Preserve mask from anomaly
    base_mask = anomaly_image.select("absolute_anomaly").mask()
    change_type = change_type.updateMask(base_mask)
    severity = severity.updateMask(base_mask)
    confidence = confidence.updateMask(base_mask)

    result = anomaly_image.addBands([change_type, severity, confidence])

    # --- ELITE FIX 3: Chain Provenance, don't overwrite ---
    # Keep all anomaly.py properties + add change properties
    return result.set({
        "processing_version": PROCESSING_VERSION,
        "threshold_config": config_name,
        "engine_chain": "anomaly->change",
        "abs_thresh_deg": cfg["abs_deg"],
        "abs_thresh_rec": cfg["abs_rec"],
        "z_thresh_deg": cfg["z_deg"],
        "z_thresh_rec": cfg["z_rec"],
        "severe_abs_thresh": cfg["severe_abs"],
        "change_classes": "{0: Stable, 1: Degradation, 2: Recovery}"
    })

def extract_change_telemetry(anomaly_image: ee.Image, classified: ee.Image, aoi: ee.Geometry, scale: int = 10):
    """Gives mentor's boardroom sentence"""
    stats = classified.select(["change_type", "change_severity", "change_confidence", "absolute_anomaly"]).reduceRegion(
        ee.Reducer.mean().combine(ee.Reducer.count(), "", True),
        geometry=aoi, scale=scale, maxPixels=1e9
    )
    return stats