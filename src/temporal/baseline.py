"""
Geo Regreen Historical Baseline Engine
Phase 2: Seasonally matched multi-year baseline.

CURRENT PERIOD (e.g. June 2026)
    ↓
Same Seasonal Window (June 2019-2025)
    ↓
Quality Filtered (cloud + CDI)
    ↓
Median
    ↓
BASELINE: NDVI_baseline, NDMI_baseline, MNDWI_baseline
"""
import ee
from src.temporal.composite import get_sentinel2_collection

SUPPORTED_INDICES = ['NDVI', 'NDMI', 'MNDWI']

def create_seasonal_baseline(
    aoi: ee.Geometry,
    month: int, # 6 = June
    start_year: int,
    end_year: int,
    seasonal_window: int = 0, # 0 = exact month, 1 = May-June-July
    indices: list = SUPPORTED_INDICES,
    max_cloud: int = 60,
    cdi_threshold: float = 0.60,
) -> ee.Image:
    """
    June 2026 baseline = median of all Junes 2019-2025 (per pixel)
    """
    # Build valid months: e.g. month=6, window=1 -> [5,6,7]
    target_months = [m for m in range(month-seasonal_window, month+seasonal_window+1) if 1 <= m <= 12]

    yearly_cols = []
    for year in range(start_year, end_year + 1):
        for m in target_months:
            start_date = ee.Date.fromYMD(year, m, 1)
            end_date = start_date.advance(1, "month")

            col = get_sentinel2_collection(
                aoi=aoi,
                start_date=start_date.format("YYYY-MM-dd"),
                end_date=end_date.format("YYYY-MM-dd"),
                max_cloud_percentage=max_cloud,
                cdi_threshold=cdi_threshold
            )
            yearly_cols.append(col)

    # Correct merge: start with first, merge rest
    multi_year_col = yearly_cols[0]
    for c in yearly_cols[1:]:
        multi_year_col = multi_year_col.merge(c)

    # Median baseline, select only indices if they exist
    baseline = multi_year_col.select(indices).median()

    # Rename to _baseline
    baseline = baseline.rename([f"{i}_baseline" for i in indices]).clip(aoi)

    return baseline.set({
        'baseline_start': start_year,
        'baseline_end': end_year,
        'baseline_month': month,
        'baseline_window': target_months,
        'baseline_type': 'seasonal_median'
    })

def get_june_baseline_example(aoi: ee.Geometry) -> ee.Image:
    """Example your mentor described"""
    return create_seasonal_baseline(
        aoi=aoi,
        month=6,
        start_year=2019,
        end_year=2025,
        seasonal_window=0
    )