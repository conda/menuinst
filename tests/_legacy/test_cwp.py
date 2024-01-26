import sys

import pytest

cwp = pytest.importorskip("menuinst._legacy.cwp", reason="Windows only")


def test_cwp(capsys):
    with pytest.raises(SystemExit):
        cwp.main([sys.prefix, "python", "-c", "print('hello')"])
        assert capsys.readouterr() == ("hello\n", "")
