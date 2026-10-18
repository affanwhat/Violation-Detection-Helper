"""Offline tests for the notebook's pure-Python helpers."""
import datetime as dt

import pytest

from notebook_loader import lib_cells


def test_lib_cells_exist():
    assert len(list(lib_cells())) >= 5


def test_lib_cells_load_without_earth_engine(nb):
    # Loading must not call Earth Engine, otherwise the cells have side effects.
    for name in ["date_windows", "make_composite", "concern_flags", "concern_zones", "zone_table"]:
        assert callable(getattr(nb, name))


@pytest.mark.parametrize(
    "date, months, expected",
    [
        (dt.date(2022, 1, 15), 3, dt.date(2022, 4, 15)),
        (dt.date(2022, 1, 31), 1, dt.date(2022, 2, 28)),
        (dt.date(2024, 1, 31), 1, dt.date(2024, 2, 29)),
        (dt.date(2022, 11, 30), 3, dt.date(2023, 2, 28)),
        (dt.date(2022, 8, 31), 6, dt.date(2023, 2, 28)),
    ],
)
def test_add_months(nb, date, months, expected):
    assert nb.add_months(date, months) == expected


def test_date_windows_six_months(nb):
    assert nb.date_windows("2022-01-01", "2024-01-01", 6) == [
        ("2022-01-01", "2022-07-01"),
        ("2022-07-01", "2023-01-01"),
        ("2023-01-01", "2023-07-01"),
        ("2023-07-01", "2024-01-01"),
    ]


def test_date_windows_truncates_last_window(nb):
    assert nb.date_windows("2022-01-01", "2022-05-15", 3) == [
        ("2022-01-01", "2022-04-01"),
        ("2022-04-01", "2022-05-15"),
    ]


def test_date_windows_do_not_drift_after_short_month(nb):
    windows = nb.date_windows("2022-01-31", "2022-07-31", 1)
    assert [end for _, end in windows] == [
        "2022-02-28",
        "2022-03-31",
        "2022-04-30",
        "2022-05-31",
        "2022-06-30",
        "2022-07-31",
    ]


def test_date_windows_are_contiguous(nb):
    windows = nb.date_windows("2021-03-17", "2025-02-02", 3)
    assert windows[0][0] == "2021-03-17"
    assert windows[-1][1] == "2025-02-02"
    for (_, end), (next_start, _) in zip(windows, windows[1:]):
        assert end == next_start


@pytest.mark.parametrize("start, end, months", [("2022-01-01", "2022-01-01", 3), ("2023-01-01", "2022-01-01", 3), ("2022-01-01", "2023-01-01", 0)])
def test_date_windows_rejects_bad_input(nb, start, end, months):
    with pytest.raises(ValueError):
        nb.date_windows(start, end, months)


def test_class_area_table_names_and_sorts(nb):
    groups = [{"class": 14, "sum": 2.5}, {"class": 15, "sum": 10.0}, {"class": 99, "sum": 1.0}]
    table = nb.class_area_table(groups, nb.BENTHIC_CLASSES)
    assert table["name"].tolist() == ["Coral/Algae", "Seagrass", "Unknown"]
    assert table["area_ha"].tolist() == [10.0, 2.5, 1.0]


def test_class_area_table_empty(nb):
    table = nb.class_area_table([], nb.GEOMORPHIC_CLASSES)
    assert table.empty
    assert list(table.columns) == ["class", "name", "area_ha"]


def _zone(zone_ha, water=0.0, veg=0.0, built=0.0, reef=0.0):
    return {
        "type": "Feature",
        "geometry": None,
        "properties": {
            "zone_ha": zone_ha,
            "water_to_land_ha": water,
            "vegetation_loss_ha": veg,
            "builtup_gain_ha": built,
            "near_reef_ha": reef,
            "lon": 106.8,
            "lat": -6.2,
        },
    }


def test_zone_table_ranks_by_signal_count_then_area(nb):
    info = {"features": [_zone(20.0, water=20.0), _zone(3.0, water=1.0, built=2.0), _zone(5.0, veg=5.0)]}
    table = nb.zone_table(info)
    assert table["signals"].tolist() == ["water_to_land, builtup_gain", "water_to_land", "vegetation_loss"]
    assert table["signal_count"].tolist() == [2, 1, 1]
    assert "near_reef_ha" in table.columns


def test_zone_table_min_signal_ignores_slivers(nb):
    info = {"features": [_zone(5.0, water=4.95, built=0.05)]}
    assert nb.zone_table(info, min_signal_ha=0.1)["signals"].tolist() == ["water_to_land"]


def test_zone_table_empty(nb):
    table = nb.zone_table({"features": []})
    assert table.empty
    assert "signals" in table.columns
