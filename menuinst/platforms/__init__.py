import sys


def menu_api_for_platform(platform=sys.platform):
    if platform == "win32":
        from .win import WindowsMenu as Menu, WindowsMenuItem as MenuItem

    elif platform == "darwin":
        from .osx import MacOSMenu as Menu, MacOSMenuItem as MenuItem

    elif platform.startswith("linux"):
        from .linux import LinuxMenu as Menu, LinuxMenuItem as MenuItem

    else:
        raise ValueError(f"platform {platform} is not supported")

    return Menu, MenuItem


Menu, MenuItem = menu_api_for_platform()