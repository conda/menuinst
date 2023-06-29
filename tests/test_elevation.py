from menuinst.utils import _test_elevation, elevate_as_needed, user_is_admin


def test_elevation(tmp_path, capfd):
    assert not user_is_admin()  # We need to start as a non-root user

    _test_elevation(str(tmp_path))
    assert capfd.readouterr().out.strip() == "user_is_admin(): False _mode: user"

    elevate_as_needed(_test_elevation)(base_prefix=str(tmp_path))
    assert capfd.readouterr().out.strip() == "user_is_admin(): True _mode: system"

    (tmp_path / ".nonadmin").touch()
    elevate_as_needed(_test_elevation)(base_prefix=str(tmp_path))
    assert capfd.readouterr().out.strip() == "user_is_admin(): False _mode: user"
