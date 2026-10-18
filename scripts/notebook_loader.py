"""Load the notebook's library cells so they can be tested outside Jupyter.

Code cells whose first line starts with ``# lib-cell:`` hold only imports,
constants and function definitions. They are executed in notebook order into a
fresh namespace, which is returned as a module-like object.
"""
import json
from pathlib import Path
from types import SimpleNamespace

NOTEBOOK = Path(__file__).resolve().parents[1] / "marine_spatial_planning_geemap.ipynb"
MARKER = "# lib-cell:"


def lib_cells(path=NOTEBOOK):
    notebook = json.loads(Path(path).read_text(encoding="utf-8"))
    for cell in notebook["cells"]:
        source = "".join(cell["source"])
        if cell["cell_type"] == "code" and source.startswith(MARKER):
            yield source


def load(path=NOTEBOOK):
    namespace = {"__name__": "notebook_lib"}
    for index, source in enumerate(lib_cells(path)):
        exec(compile(source, f"{Path(path).name}[lib-cell {index}]", "exec"), namespace)
    return SimpleNamespace(**namespace)
