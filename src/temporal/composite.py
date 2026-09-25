"""
Geo Regreen Temporal Composite Engine
Phase 2: Sentinel-2 temporal filtering + median composites
Elite Build — cloud-masked, analysis-ready
"""
import ee

# ── Constants ──────────────────────────────────────────────
S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
CLOUD_SCORE_COLLECTION = "GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED"
DEFAULT_CLEAR_THRESHOLD = 0.60

# ── Core Engine ────────────────────────────────────────────
def get_sentinel2_collection(
    aoi: ee.Geometry,
    start_date: str,
    end_date: str,
    max_cloud_percentage: int = 60,
    clear_threshold: float = DEFAULT_CLEAR_THRESHOLD,
) -> ee.ImageCollection:
    """
    Build cloud-masked Sentinel-2 SR collection using Cloud Score+.
    """
    s2 = (
        ee.ImageCollection(S2_COLLECTION)
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud_percentage))
    )

    cloud_score = ee.ImageCollection(CLOUD_SCORE_COLLECTION)
    joined = s2.linkCollection(cloud_score, ["cs_cdf"])

    def apply_quality_mask(image: ee.Image) -> ee.Image:
        clear = image.select("cs_cdf").gte(clear_threshold)
        return image.updateMask(clear).copyProperties(image, image.propertyNames())

    return joined.map(apply_quality_mask)

def create_median_composite(collection: ee.ImageCollection) -> ee.Image:
    """Median composite - removes clouds/shadows."""
    return collection.median()

def create_index_composite(
    collection: ee.ImageCollection,
    index_function,
    index_name: str,
) -> ee.Image:
    """Map an index function (NDVI, MNDWI, etc.) then median."""
    index_collection = collection.map(index_function)
    return index_collection.median().rename(index_name)

def collection_count(collection: ee.ImageCollection) -> ee.Number:
    """Return number of images in collection."""
    return collection.size()