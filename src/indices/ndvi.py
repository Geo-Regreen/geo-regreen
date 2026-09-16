import ee

def calculate_ndvi(image: ee.Image) -> ee.Image:
    """
    Calculates the Normalized Difference Vegetation Index (NDVI)
    using Sentinel-2 NIR (B8) and Red (B4) bands.
    """
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    return ndvi