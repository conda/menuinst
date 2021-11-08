from pathlib import Path
import shutil
import os

import pytest

from menuinst.schema import platform_key

DATA = Path(__file__).parent / "data"
PLATFORM = platform_key()

os.environ["PYTEST_IN_USE"] = "1"


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
