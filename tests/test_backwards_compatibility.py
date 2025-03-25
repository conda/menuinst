import os

import pytest

from conftest import DATA, LEGACY

if os.name != "nt":
    pytest.skip("Windows only", allow_module_level=True)


def test_import_paths():
    """Imports used by conda <=23.7.2. Ensure they still work."""
    import menuinst._legacy.cwp  # noqa: F401
    import menuinst._legacy.main  # noqa: F401
    import menuinst._legacy.utils  # noqa: F401
    import menuinst._legacy.win32  # noqa: F401
    from menuinst import install  # noqa: F401
    from menuinst.knownfolders import FOLDERID, get_folder_path  # noqa: F401
    from menuinst.win32 import dirs_src  # noqa: F401
    from menuinst.win_elevate import isUserAdmin, runAsAdmin  # noqa: F401
    from menuinst.winshortcut import create_shortcut  # noqa: F401


@pytest.mark.skipif("CI" not in os.environ, reason="Only run on CI. Export CI=1 to run locally.")
@pytest.mark.parametrize(
    "json_path",
    [
        pytest.param(str(DATA / "jsons" / "sys-prefix.json"), id="v2"),
        pytest.param(str(LEGACY / "sys-prefix.json"), id="v1"),
    ],
)
def test_install_prefix_compat(tmp_path, json_path):
    from menuinst.api import _install_adapter

    (tmp_path / ".nonadmin").touch()
    _install_adapter(json_path, prefix=tmp_path)
    _install_adapter(json_path, remove=True, prefix=tmp_path)
