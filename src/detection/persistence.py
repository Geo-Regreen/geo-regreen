"""
Geo Regreen Detection Engine - Persistence
Engine: GeoRegreen Engine 0.1.0

Purpose:
    Turn a one-time flag into defensible evidence.
    Answers: Has this held steady? Since when? How often?

Fixes:
    - Direction-aware: degradation vs recovery counted separately
    - Temporal telemetry: first_seen, last_seen, persistence
    - Server-safe, provenance-chain safe
"""

from __future__ import annotations
import ee
from typing import Dict, List

PROCESSING_VERSION = "GeoRegreen Engine 0.1.0"

BAND_COUNT = "persistence_count"
BAND_COUNT_DEG = "persistence_deg_count"
BAND_COUNT_REC = "persistence_rec_count"
BAND_SCORE = "persistence_score"
BAND_FIRST = "persistence_first_seen"
BAND_LAST = "persistence_last_seen"

def add_persistence(
    classified_collection: ee.ImageCollection,
    min_observations: int = 2,
    change_band: str = "change_type",
) -> ee.ImageCollection:
    """
    Direction-aware persistence.

    Expects: collection output from change.py
      change_type: 0=Stable, 1=Degradation, 2=Recovery

    Returns: same collection, each image gets persistent summary bands attached
    + final summary image via summarize_persistence()
    """
    collection = ee.ImageCollection(classified_collection)
    min_obs = ee.Number(max(int(min_observations), 1))

    def flag(image: ee.Image) -> ee.Image:
        img = ee.Image(image)
        ct = img.select(change_band)

        deg = ct.eq(1).rename("flag_deg")
        rec = ct.eq(2).rename("flag_rec")
        any_flag = ct.neq(0).rename("flag_any")

        # Encode time as days since epoch for first/last calc
        time = img.date().millis().divide(1000*3600*24).rename("time_days")

        return ee.Image.cat([deg, rec, any_flag, time]).copyProperties(img, ["system:time_start"])

    flags = collection.map(flag)

    # Sums
    deg_count = flags.select("flag_deg").sum().rename(BAND_COUNT_DEG)
    rec_count = flags.select("flag_rec").sum().rename(BAND_COUNT_REC)
    total_count = flags.select("flag_any").sum().rename(BAND_COUNT)

    # First seen / Last seen = min/max time where flag_any = 1
    time_masked = flags.map(lambda i: ee.Image(i).select("time_days").updateMask(ee.Image(i).select("flag_any")))

    first_seen = time_masked.min().rename(BAND_FIRST)
    last_seen = time_masked.max().rename(BAND_LAST)

    # Valid mask: meets min observations
    valid = total_count.gte(min_obs)

    deg_count = deg_count.updateMask(valid)
    rec_count = rec_count.updateMask(valid)
    total_count = total_count.updateMask(valid)
    first_seen = first_seen.updateMask(valid)
    last_seen = last_seen.updateMask(valid)

    # Summary image - THIS is what you show board
    summary = ee.Image.cat([
        total_count, deg_count, rec_count, first_seen, last_seen
    ]).set({
        "processing_version": PROCESSING_VERSION,
        "engine": "persistence",
        "engine_chain": "anomaly->change->persistence",
        "min_observations": min_obs,
        "persistence_bands": f"{BAND_COUNT}, {BAND_COUNT_DEG}, {BAND_COUNT_REC}, {BAND_FIRST}, {BAND_LAST}",
        "definition": f"Persistence = count of flagged observations >= {min_obs.getInfo() if False else min_observations}"
    })

    # Attach summary bands to each image (so downstream risk can use)
    def attach(image: ee.Image) -> ee.Image:
        img = ee.Image(image)
        return img.addBands([total_count, deg_count, rec_count]).setMulti({
            "processing_version": PROCESSING_VERSION,
            "min_observations": min_obs,
            "engine_chain": "anomaly->change->persistence"
        }).copyProperties(img, ["system:time_start"], True)

    collection_with_bands = collection.map(attach)

    # Store summary as property of collection for retrieval
    return collection_with_bands.set("persistence_summary", summary)

def summarize_persistence(persistent_collection: ee.ImageCollection) -> ee.Image:
    """Get the boardroom summary image"""
    return ee.Image(persistent_collection.get("persistence_summary"))

def calculate_persistence_score(
    persistence_image: ee.Image,
    expected_observations: int,
    count_band: str = BAND_COUNT
) -> ee.Image:
    """
    Convert count -> 0.0 to 1.0 score.
    For risk/confidence.py weighting.

    score = count / expected, capped at 1.0
    """
    expected = ee.Number(max(int(expected_observations), 1))

    score = (
        ee.Image(persistence_image)
        .select(count_band)
        .divide(expected)
        .clamp(0, 1)
        .rename(BAND_SCORE)
    )

    # Duration in days
    first = persistence_image.select(BAND_FIRST)
    last = persistence_image.select(BAND_LAST)
    duration = last.subtract(first).rename("persistence_duration_days")

    return ee.Image.cat([score, duration]).copyProperties(
        persistence_image,
        persistence_image.propertyNames()
    )

def extract_persistence_telemetry(summary_image: ee.Image, aoi: ee.Geometry, scale: int = 10) -> Dict:
    """Mentor telemetry: Persistence: 3 obs, First: 2026-06-10, Last: 2026-06-30"""
    stats = summary_image.reduceRegion(
        ee.Reducer.mean(),
        geometry=aoi, scale=scale, maxPixels=1e9
    )
    return stats