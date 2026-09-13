# Marine Spatial Planning Violation Signals

Starter project for detecting remote-sensing indicators that may suggest marine spatial planning violations.

This project does **not** determine legal violations by itself. It produces geospatial evidence layers and summaries that can support review by planners, regulators, or domain experts.

## Initial Inputs

- Area of interest: user-drawn polygon in `geemap`, uploaded vector data, or administrative boundary.
- Start date.
- End date.
- Time interval: 3 or 6 months.

## Initial Outputs

1. Cloud-masked Sentinel-2 time series between the start and end dates.
2. NDVI, NDWI, and NDBI change maps between start and end dates.
3. Land/water area change using NDWI.
4. Existing coral reef map using Allen Coral Atlas data when available.
5. Candidate business/entity search notes for the area.

## Recommended First Workflow

1. Define the area of interest.
2. Build cloud-masked Sentinel-2 composites for each interval.
3. Calculate indices for every composite.
4. Compare start and end composites.
5. Flag potential concern zones:
   - water converted to land,
   - vegetation loss,
   - built-up expansion,
   - development near mapped coral reef,
   - development inside protected or restricted zones if planning layers are available.
6. Export maps and summary tables.

## Data Sources

- Sentinel-2 Surface Reflectance Harmonized: `COPERNICUS/S2_SR_HARMONIZED`
- Sentinel-2 Cloud Probability: `COPERNICUS/S2_CLOUD_PROBABILITY`
- Allen Coral Atlas: availability depends on Earth Engine catalog access and region coverage.
- Marine planning/protected-area layers: should be added per country or region.
- Business entities: likely requires external APIs or manual registry data, not Earth Engine alone.

## Files

- `marine_spatial_planning_geemap.ipynb`: Colab/Jupyter notebook workflow using `geemap`.
- `gee_starter.js`: Earth Engine Code Editor starter script.
- `requirements.txt`: Python packages for Colab/local use.

## Next Improvements

- Add official zoning/planning layers for the target country.
- Add automated exports to Google Drive.
- Add per-year change summaries.
- Add confidence scoring for each red-flag zone.
- Add report generation with maps, charts, and tables.
