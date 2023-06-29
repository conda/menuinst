import os

from menuinst.utils import elevate_as_needed, _test_elevation


def test_elevation(tmp_path, capfd):
    assert os.getuid() != 0  # We need to start as a non-root user

    _test_elevation(str(tmp_path))
    assert capfd.readouterr().out.strip() == "user_is_admin(): False _mode: user"

    elevate_as_needed(_test_elevation)(base_prefix=str(tmp_path))
    assert capfd.readouterr().out.strip() == "user_is_admin(): True _mode: system"

    (tmp_path / ".nonadmin").touch()
    elevate_as_needed(_test_elevation)(base_prefix=str(tmp_path))
    assert capfd.readouterr().out.strip() == "user_is_admin(): False _mode: user"
