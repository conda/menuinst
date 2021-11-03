import sys

_PLATFORMS = "windows", "osx", "linux"


def menu_for_platform(platform=sys.platform):
    assert platform in (
        "windows",
        "osx",
        "linux",
    ), f"`platform` must be one of {_PLATFORMS}"
    if platform == "windows":
        from .windows import WindowsMenu as Menu

    if platform == "osx":
        from .osx import MacOSMenu as Menu

    if platform == "linux":
        from .linux import LinuxMenu as Menu

    return Menu


PlatformMenu = menu_for_platform()
