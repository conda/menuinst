import os

from menuinst.utils import _test_elevation, elevate_as_needed, user_is_admin


def test_elevation(tmp_path, capfd):
    if os.name == "nt":
        on_ci = os.environ.get("CI")
        is_admin = user_is_admin()
        if not on_ci:
            # Windows runners on GHA always run as admin
            assert not is_admin

        _test_elevation(str(tmp_path))
        output = (tmp_path / "_test_output.txt").read_text().strip()
        if on_ci:
            assert output.endswith("_mode: user")
        else:
            assert output.endswith("user_is_admin(): False _mode: user")

        elevate_as_needed(_test_elevation)(base_prefix=str(tmp_path))
        output = (tmp_path / "_test_output.txt").read_text().strip()
        if on_ci:
            assert output.endswith("_mode: system")
        else:
            assert output.endswith("user_is_admin(): True _mode: system")
    else:
        assert not user_is_admin()  # We need to start as a non-root user

        _test_elevation(str(tmp_path))
        assert capfd.readouterr().out.strip() == "user_is_admin(): False _mode: user"

        elevate_as_needed(_test_elevation)(base_prefix=str(tmp_path))
        assert capfd.readouterr().out.strip() == "user_is_admin(): True _mode: system"

        (tmp_path / ".nonadmin").touch()
        elevate_as_needed(_test_elevation)(base_prefix=str(tmp_path))
        assert capfd.readouterr().out.strip() == "user_is_admin(): False _mode: user"
