"""Live Earth Engine tests. Skipped unless EE_PROJECT is set.

Set EE_PROJECT in .env (see .env.example) or the environment, then run:  pytest scripts
"""
import pytest

# Small box on the north Jakarta coast: reclamation islands, port and urban land.
JAKARTA_COAST = [[106.74, -6.09], [106.80, -6.09], [106.80, -6.13], [106.74, -6.13], [106.74, -6.09]]
# Pulau Pari, Thousand Islands: mapped reef in the Allen Coral Atlas.
PULAU_PARI = [[106.59, -5.85], [106.63, -5.85], [106.63, -5.87], [106.59, -5.87], [106.59, -5.85]]
# Open South Pacific with no Sentinel-2 acquisitions.
OPEN_OCEAN = [[-130.0, -40.0], [-129.9, -40.0], [-129.9, -40.1], [-130.0, -40.1], [-130.0, -40.0]]


@pytest.fixture(scope="module")
def jakarta(ee_session):
    return ee_session.Geometry.Polygon([JAKARTA_COAST])


@pytest.fixture(scope="module")
def composites(nb, jakarta):
    windows = [("2019-06-01", "2019-12-01"), ("2023-06-01", "2023-12-01")]
    return [nb.make_composite(jakarta, start, end) for start, end in windows]


def test_window_image_counts(nb, ee_session, jakarta):
    windows = nb.date_windows("2023-01-01", "2024-01-01", 6)
    counts = nb.window_image_counts(jakarta, windows)
    assert len(counts) == 2
    assert all(count > 0 for count in counts)


def test_window_image_counts_empty_window(nb, ee_session):
    ocean = ee_session.Geometry.Polygon([OPEN_OCEAN])
    assert nb.window_image_counts(ocean, [("2023-01-01", "2023-07-01")]) == [0]


def test_composite_has_reflectance_and_indices(nb, composites):
    bands = composites[0].bandNames().getInfo()
    assert {"B2", "B3", "B4", "B8", "B11", "NDVI", "NDWI", "NDBI"} <= set(bands)
    assert "SCL" not in bands


def test_time_series_table(nb, composites, jakarta):
    table = nb.time_series_table(composites, jakarta)
    assert len(table) == 2
    assert table["window_start"].tolist() == ["2019-06-01", "2023-06-01"]
    assert table["clear_fraction"].between(0, 1.01).all()
    assert (table["water_ha"] >= 0).all()


def test_concern_zones(nb, composites, jakarta):
    flags = nb.concern_flags(*composites)
    assert flags.bandNames().getInfo() == nb.FLAG_BANDS
    zones = nb.concern_zones(flags, jakarta, near_reef=nb.near_reef_mask(500), min_area_ha=1.0, max_zones=20)
    table = nb.zone_table(zones.getInfo())
    assert len(table) > 0, "the Jakarta coast should show some change between 2019 and 2023"
    assert (table["zone_ha"] >= 1.0).all()
    assert {"signals", "signal_count", "near_reef_ha", "lon", "lat"} <= set(table.columns)


def test_coral_class_areas(nb, ee_session):
    pari = ee_session.Geometry.Polygon([PULAU_PARI])
    groups = nb.class_area_groups(nb.coral_atlas().select("geomorphic"), pari).getInfo()
    table = nb.class_area_table(groups, nb.GEOMORPHIC_CLASSES)
    assert table["area_ha"].sum() > 0
    assert "Unknown" not in table["name"].tolist()
