import ee
from src.temporal.composite import get_sentinel2_collection, create_median_composite, collection_count
ee.Initialize(project="geo-regreen-01")
aoi = ee.Geometry.Rectangle([28.00, -26.30, 28.20, -26.10])
col = get_sentinel2_collection(aoi, "2026-01-01", "2026-03-31", 60, 0.60)
print("Observations:", col.size().getInfo())
print("Bands:", create_median_composite(col).bandNames().getInfo())
print("TEMPORAL ENGINE WORKING")