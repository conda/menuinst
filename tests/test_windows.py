import sys

import pytest

pytestmark = pytest.mark.skipif(not sys.platform == "win32", reason="Only Windows")


def test_file_extensions():
    pass

def test_protocols():
    pass
