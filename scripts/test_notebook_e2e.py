"""End-to-end run of the whole notebook in a headless kernel. Skipped unless EE_PROJECT is set.

The install cell is dropped, the parameters are shrunk to a small AOI and coarse scale so the
run takes minutes, and a final cell checks the main outputs. Any failing cell fails the test
with that cell's traceback. The executed notebook, with every cell's output, is always written to
scripts/output/ (git-ignored) so the results can be reviewed in Jupyter or VS Code.
"""
import os

import nbformat
import pytest
from nbclient import NotebookClient

from notebook_loader import NOTEBOOK

OUTPUT = NOTEBOOK.parent / "scripts" / "output" / NOTEBOOK.name.replace(".ipynb", ".executed.ipynb")

# Same north Jakarta coast box as test_earth_engine.py: reclamation between 2019 and 2023.
OVERRIDES = """\
# Injected by scripts/test_notebook_e2e.py
START_DATE = "2019-01-01"
END_DATE = "2024-01-01"
INTERVAL_MONTHS = 12
FALLBACK_COORDS = [[106.74, -6.09], [106.80, -6.09], [106.80, -6.13], [106.74, -6.13], [106.74, -6.09]]
MAP_CENTER = [-6.11, 106.77]
MIN_ZONE_AREA_HA = 1.0
ANALYSIS_SCALE = 30
"""

CHECKS = """\
# Injected by scripts/test_notebook_e2e.py
assert baseline_water_ha > 0
assert len(time_series) == len(valid_windows) > 0
assert time_series["lost_fraction"].between(0, 1.0).all()
assert lost_stats["baseline_water_ha"] > 0
assert len(zone_df) > 0, "the Jakarta coast should show some reclamation between 2019 and 2023"
assert {"signals", "signal_count", "zone_ha", "near_reef_ha", "lon", "lat"} <= set(zone_df.columns)
"""


def prepared_notebook():
    nb = nbformat.read(NOTEBOOK, as_version=4)
    nb.cells = [cell for cell in nb.cells if not cell.source.startswith("%pip")]
    params = next(i for i, cell in enumerate(nb.cells) if cell.source.startswith("START_DATE = "))
    nb.cells.insert(params + 1, nbformat.v4.new_code_cell(OVERRIDES))
    nb.cells.append(nbformat.v4.new_code_cell(CHECKS))
    return nb


def test_prepared_notebook_overrides_follow_parameters():
    # Offline: the parameters cell must define everything the overrides replace, so later cells see them.
    nb = prepared_notebook()
    params = next(i for i, cell in enumerate(nb.cells) if cell.source.startswith("START_DATE = "))
    assert nb.cells[params + 1].source == OVERRIDES
    for name in ["FALLBACK_COORDS", "MAP_CENTER", "ANALYSIS_SCALE"]:
        assert f"{name} = " in nb.cells[params].source
        assert not any(f"{name} = " in cell.source for cell in nb.cells[params + 2 :])
    assert not any(cell.source.startswith("%pip") for cell in nb.cells)


@pytest.mark.skipif(not os.environ.get("EE_PROJECT"), reason="EE_PROJECT not set; skipping notebook run")
def test_notebook_runs_end_to_end(monkeypatch):
    monkeypatch.setenv("EE_NONINTERACTIVE", "1")  # the kernel inherits it; auth errors raise instead of prompting
    nb = prepared_notebook()
    client = NotebookClient(
        nb, timeout=900, kernel_name="python3", resources={"metadata": {"path": str(NOTEBOOK.parent)}}
    )
    try:
        client.execute()
    finally:
        OUTPUT.parent.mkdir(exist_ok=True)
        nbformat.write(nb, OUTPUT)
        print(f"\nExecuted notebook saved to {OUTPUT}")
