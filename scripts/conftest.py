import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from notebook_loader import load

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


@pytest.fixture(scope="session")
def nb():
    return load()


@pytest.fixture(scope="session")
def ee_session(nb):
    """Initialized Earth Engine. Set EE_PROJECT in .env or the environment to run these tests."""
    project = os.environ.get("EE_PROJECT")
    if not project:
        pytest.skip("EE_PROJECT not set; skipping Earth Engine tests")
    nb.ee.Initialize(project=project)
    return nb.ee
