import ee

def calculate_ndmi(image: ee.Image) -> ee.Image:
    """
    Calculates the Normalized Difference Moisture Index (NDMI)
    using Sentinel-2 NIR (B8) and SWIR1 (B11) bands.
    """
    ndmi = image.normalizedDifference(['B8', 'B11']).rename('NDMI')
    return ndmi