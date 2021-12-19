from pathlib import Path
import shutil
import os
import json
from subprocess import check_output
from tempfile import TemporaryDirectory

import py
import pytest

from menuinst.schema import platform_key

os.environ["PYTEST_IN_USE"] = "1"
DATA = Path(__file__).parent / "data"
PLATFORM = platform_key()


def base_prefix():
    prefix = os.environ.get("CONDA_ROOT", os.environ.get("MAMBA_ROOT_PREFIX"))
    if not prefix:
        prefix = json.loads(check_output(["conda", "info", "--json"]))["root_prefix"]
    return prefix


BASE_PREFIX = base_prefix()


@pytest.fixture()
def delete_files():
    paths = []
    yield paths
    for path in paths:
        path = Path(path)
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


@pytest.fixture(scope="function")
def tmpdir(tmpdir, request):
    tmpdir = TemporaryDirectory(dir=str(tmpdir))
    request.addfinalizer(tmpdir.cleanup)
    return py.path.local(tmpdir.name)
