"""
Geo Regreen Temporal Time-Series Engine
Phase 2: Monthly stacks + EO index time-series

Pipeline:
    composite.py (S2 + CloudScore+)
        ↓
    timeseries.py (this file - temporal resampling)
        ↓
    baseline.py / anomaly.py
"""
import ee
from typing import Callable
from src.temporal.composite import get_sentinel2_collection, create_median_composite

# ─────────────────────────────────────────────
# 1. Core: Add Index to Every Image
# ─────────────────────────────────────────────
def add_index_to_collection(
    collection: ee.ImageCollection,
    index_fn: Callable[[ee.Image], ee.Image],
) -> ee.ImageCollection:

    def _calc(img: ee.Image) -> ee.Image:
        idx = index_fn(img)
        return idx.set({
            "system:time_start": img.get("system:time_start"),
            "system:index": img.get("system:index"),
            "CLOUDY_PIXEL_PERCENTAGE": img.get("CLOUDY_PIXEL_PERCENTAGE"),
        })

    return collection.map(_calc)

# ─────────────────────────────────────────────
# 2. Core: Build Index Time Series (NDVI/MNDWI/EVI)
# ─────────────────────────────────────────────
def build_index_time_series(
    aoi: ee.Geometry,
    start_date: str,
    end_date: str,
    index_fn: Callable[[ee.Image], ee.Image],
    max_cloud: int = 60,
    cdi_threshold: float = 0.60,
) -> ee.ImageCollection:

    s2 = get_sentinel2_collection(aoi, start_date, end_date, max_cloud, cdi_threshold)
    return add_index_to_collection(s2, index_fn)

# ─────────────────────────────────────────────
# 3. Elite: Monthly Median Stack (For Charts + Baseline)
# ─────────────────────────────────────────────
def get_monthly_stack(
    aoi: ee.Geometry,
    start_date: str,
    end_date: str,
    max_cloud: int = 60,
    cdi_threshold: float = 0.60,
) -> ee.ImageCollection:

    start = ee.Date(start_date)
    end = ee.Date(end_date)
    n_months = end.difference(start, "month").ceil()

    def _monthly(m: ee.Number) -> ee.Image:
        m = ee.Number(m)
        m_start = start.advance(m, "month")
        m_end = m_start.advance(1, "month")

        col = get_sentinel2_collection(
            aoi,
            m_start.format("YYYY-MM-dd"),
            m_end.format("YYYY-MM-dd"),
            max_cloud,
            cdi_threshold,
        )

        return create_median_composite(col).set({
            "system:time_start": m_start.millis(),
            "date": m_start.format("YYYY-MM"),
            "year": m_start.get("year"),
            "month": m_start.get("month"),
            "count": col.size(),
        }).clip(aoi)

    return ee.ImageCollection(ee.List.sequence(0, n_months.subtract(1)).map(_monthly))

# ─────────────────────────────────────────────
# 4. Helpers: QA / Chart
# ─────────────────────────────────────────────
def get_observation_dates(col: ee.ImageCollection) -> ee.List:
    return col.aggregate_array("system:time_start")

def get_observation_count(col: ee.ImageCollection) -> ee.Number:
    return col.size()

def get_stack_count(stack: ee.ImageCollection) -> ee.Number:
    """How many monthly composites built"""
    return stack.size()
# ─────────────────────────────────────────────
# 5. Elite: AOI-Level Stats (Mentor's Requirement)
# ─────────────────────────────────────────────
def get_aoi_time_series(
    monthly_stack: ee.ImageCollection,
    aoi: ee.Geometry,
    scale: int = 10,
) -> ee.FeatureCollection:
    """
    Collapses each monthly composite into 1 mean value over AOI
    Returns: Date  NDVI  -> ready for Chart.js
    """

    def _reduce(img: ee.Image) -> ee.Feature:
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
        stats = img.addBands(ndvi, overwrite=True).reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=scale,
            maxPixels=1e13,
            bestEffort=True,
        )

        return ee.Feature(None, {
            "date": img.get("date"),
            "NDVI": stats.get("NDVI"),
            "count": img.get("count"),
            "system:time_start": img.get("system:time_start"),
        })

    return monthly_stack.map(_reduce)