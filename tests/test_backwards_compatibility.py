import os

import pytest


@pytest.mark.skipif(os.name != "nt", reason="Windows only")
def test_import_paths():
    """Imports used by conda <=23.7.2. Ensure they still work."""
    # ensure apipkg generated submodules work
    from menuinst import install  # noqa: F401
    from menuinst.knownfolders import FOLDERID, get_folder_path  # noqa: F401
    from menuinst.win32 import dirs_src  # noqa: F401
    from menuinst.winshortcut import create_shortcut  # noqa: F401
    from menuinst.win_elevate import runAsAdmin, isUserAdmin  # noqa: F401

    # ensure legacy submodules work
    import menuinst._legacy.cwd  # noqa: F401
    import menuinst._legacy.main  # noqa: F401
    import menuinst._legacy.utils  # noqa: F401
    import menuinst._legacy.win32  # noqa: F401
