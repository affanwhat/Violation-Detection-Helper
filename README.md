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
- `scripts/`: tests for the notebook's helper functions.

## Testing

The notebook stays self-contained for Colab. Code cells whose first line is `# lib-cell: ...` contain only imports, constants and function definitions; `scripts/notebook_loader.py` executes exactly those cells so the tests can call the same functions the notebook uses.

```bash
pip install -r requirements-dev.txt
cp .env.example .env   # then set EE_PROJECT
pytest scripts
```

Without `EE_PROJECT` only the offline tests run. Live tests need `earthengine authenticate` and a Google Cloud project registered for Earth Engine. The notebook reads the same `.env` when run locally; in Colab, set `EE_PROJECT` in the initialization cell.

## Status

Implemented in the notebook: cloud-masked time series, per-window index and water-area summary, NDVI/NDWI/NDBI change maps, land/water change, Allen Coral Atlas (`ACA/reef_habitat/v2_0`) reef habitat, and rule-based concern zones (water to land, vegetation loss, built-up gain, near reef).

`gee_starter.js` covers only the change maps and land/water change.

## Next Improvements

- Confidence scoring for each concern zone.
- Candidate business/entity lookup via OpenStreetMap/Overpass.
- Protected areas (WDPA) and country zoning layers, starting with Indonesia's RZWP3K.
- Automated exports to Google Drive.
- HTML and PDF report generation with maps, charts, and tables.
