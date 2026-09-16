import ee

def calculate_mndwi(image: ee.Image) -> ee.Image:
    """
    Calculates the Modified Normalized Difference Water Index (MNDWI)
    using Sentinel-2 Green (B3) and SWIR1 (B11) bands.
    """
    mndwi = image.normalizedDifference(['B3', 'B11']).rename('MNDWI')
    return mndwi