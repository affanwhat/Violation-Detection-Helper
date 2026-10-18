// Earth Engine Code Editor starter for marine spatial planning signals.
// The analysis is limited to baseline water: pixels that are water by NDWI in the
// base period (START_DATE + BASELINE_MONTHS). Land in the base period is ignored.

var START_DATE = '2021-01-01';
var END_DATE = '2025-01-01';
var INTERVAL_MONTHS = 6;
var BASELINE_MONTHS = 12;
var CLOUD_PROBABILITY_THRESHOLD = 40;
var NDWI_THRESHOLD = 0.0;

// Replace this polygon with the user-defined area of interest.
var aoi = ee.Geometry.Polygon([
  [
    [106.70, -6.10],
    [106.90, -6.10],
    [106.90, -6.30],
    [106.70, -6.30],
    [106.70, -6.10]
  ]
]);

Map.centerObject(aoi, 11);
Map.addLayer(aoi, {color: 'yellow'}, 'AOI');

function maskS2Clouds(image) {
  var cloudProb = ee.Image(image.get('cloud_mask')).select('probability');
  var scl = image.select('SCL');

  var clearCloudProb = cloudProb.lt(CLOUD_PROBABILITY_THRESHOLD);
  var clearScl = scl.neq(3)
    .and(scl.neq(8))
    .and(scl.neq(9))
    .and(scl.neq(10))
    .and(scl.neq(11));

  return image
    .updateMask(clearCloudProb.and(clearScl))
    .divide(10000)
    .copyProperties(image, ['system:time_start']);
}

function sentinel2Collection(startDate, endDate) {
  var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(aoi)
    .filterDate(startDate, endDate);

  var clouds = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
    .filterBounds(aoi)
    .filterDate(startDate, endDate);

  var joined = ee.ImageCollection(ee.Join.saveFirst('cloud_mask').apply({
    primary: s2,
    secondary: clouds,
    condition: ee.Filter.equals({
      leftField: 'system:index',
      rightField: 'system:index'
    })
  }));

  return joined.map(maskS2Clouds);
}

function addIndices(image) {
  var ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI');
  var ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI');
  var ndbi = image.normalizedDifference(['B11', 'B8']).rename('NDBI');
  return image.addBands([ndvi, ndwi, ndbi]);
}

function advanceDate(date, months) {
  return ee.Date(date).advance(months, 'month');
}

var baselineComposite = addIndices(
  sentinel2Collection(START_DATE, advanceDate(START_DATE, BASELINE_MONTHS))
    .median()
    .clip(aoi)
);

var endComposite = addIndices(
  sentinel2Collection(ee.Date(END_DATE).advance(-INTERVAL_MONTHS, 'month'), END_DATE)
    .median()
    .clip(aoi)
);

// Cloud gaps in the base period count as not water, so they are left out.
var baselineWater = baselineComposite.select('NDWI').gt(NDWI_THRESHOLD)
  .unmask(0)
  .rename('baseline_water');

var ndviChange = endComposite.select('NDVI')
  .subtract(baselineComposite.select('NDVI'))
  .updateMask(baselineWater)
  .rename('NDVI_change');

var ndwiChange = endComposite.select('NDWI')
  .subtract(baselineComposite.select('NDWI'))
  .updateMask(baselineWater)
  .rename('NDWI_change');

var ndbiChange = endComposite.select('NDBI')
  .subtract(baselineComposite.select('NDBI'))
  .updateMask(baselineWater)
  .rename('NDBI_change');

var endWater = endComposite.select('NDWI').gt(NDWI_THRESHOLD);
var waterToLand = endWater.not().updateMask(baselineWater).rename('water_to_land');

var pixelAreaHa = ee.Image.pixelArea().divide(10000);
var changeAreaHa = ee.Image.cat([
  baselineWater.multiply(pixelAreaHa).rename('baseline_water_ha'),
  waterToLand.multiply(pixelAreaHa).rename('water_to_land_ha')
]).reduceRegion({
  reducer: ee.Reducer.sum(),
  geometry: aoi,
  scale: 10,
  maxPixels: 1e13
});

print('Baseline water and water lost by the end, ha', changeAreaHa);

Map.addLayer(
  baselineComposite,
  {bands: ['B4', 'B3', 'B2'], min: 0, max: 0.3},
  'Baseline true color'
);
Map.addLayer(
  endComposite,
  {bands: ['B4', 'B3', 'B2'], min: 0, max: 0.3},
  'End true color'
);
Map.addLayer(
  baselineWater.selfMask(),
  {palette: ['blue'], opacity: 0.4},
  'Baseline water'
);
Map.addLayer(
  ndviChange,
  {min: -0.5, max: 0.5, palette: ['brown', 'white', 'green']},
  'NDVI change'
);
Map.addLayer(
  ndwiChange,
  {min: -0.5, max: 0.5, palette: ['red', 'white', 'blue']},
  'NDWI change'
);
Map.addLayer(
  ndbiChange,
  {min: -0.5, max: 0.5, palette: ['blue', 'white', 'red']},
  'NDBI change'
);
Map.addLayer(
  waterToLand.selfMask(),
  {palette: ['red']},
  'Water to land'
);

// Allen Coral Atlas and business/entity lookup are intentionally placeholders.
// Add those after confirming region-specific asset IDs and external data sources.
