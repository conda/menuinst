import os

import pytest

@pytest.mark.skipif(os.name != "nt", reason="Windows only")
def test_import_paths():
    "These import paths are/were used by conda <=23.7.2. Ensure they still work."
    from menuinst.win32 import dirs_src
    from menuinst.knownfolders import FOLDERID, get_folder_path
    from menuinst.winshortcut import create_shortcut