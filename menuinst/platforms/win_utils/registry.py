"""
Utilities for Windows Registry manipulation
"""
from logging import getLogger
from subprocess import run
import winreg

log = getLogger(__name__)


def _reg_exe(*args, check=True):
    p = run(["reg.exe", *args, "/f"], capture_output=True, text=True)
    log.debug("Ran reg.exe with args %s", args)
    log.debug("Return: %s", p.returncode)
    log.debug("Stdout:\n%s", p.stdout)
    log.debug("Stderr:\n%s", p.stderr)
    if check:
        p.check_returncode()
    return p


def register_file_extension(extension, identifier, command, icon=None, mode="user"):
    with winreg.OpenKeyEx(
        winreg.HKEY_LOCAL_MACHINE
        if mode == "system"
        else winreg.HKEY_CURRENT_USER,
        r"Software\Classes"
    ) as key:
        # First we associate an extension with a handler
        winreg.SetValue(key, extension, winreg.REG_SZ, identifier)
        log.debug("Created registry entry for extension '%s'", extension)

        # Now we register the handler
        handler_desc = f"{extension} {identifier} handler"
        winreg.SetValue(key, identifier, winreg.REG_SZ, handler_desc)
        log.debug("Created registry entry for handler '%s'", identifier)

        # and set the 'open' command
        subkey = rf"{identifier}\shell\open\command"
        winreg.SetValue(key, subkey, winreg.REG_SZ, command)
        log.debug("Created registry entry for command '%s'", command)

        if icon:
            winreg.SetValue(key, fr"{identifier}\DefaultIcon", winreg.REG_SZ, icon)
            log.debug("Created registry entry for icon '%s'", icon)

        # TODO: We can add contextual menu items too
        # via f"{handler_key}\shell\<Command Title>\command"


def unregister_file_extension(extension, identifier, mode="user"):
    root, root_str = (winreg.HKEY_LOCAL_MACHINE, "HKLM") if mode == "system" else (winreg.HKEY_CURRENT_USER, "HKCU")
    _reg_exe("delete", fr"{root_str}\Software\Classes\{identifier}")

    try:
        with winreg.OpenKeyEx(root, r"Software\Classes") as key:
            value, _  = winreg.QueryValueEx(key, "")
            delete_extension = value == identifier
    except OSError as exc:
        log.exception("Could not check key %s for deletion", extension, exc_info=exc)
        return

    if delete_extension:
        _reg_exe("delete", fr"{root_str}\Software\Classes\{extension}")


def register_url_protocol(protocol, command, identifier=None, icon=None, mode="user"):
    if mode == "system":
        key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, protocol)
    else:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, fr"Software\Classes\{protocol}")
    with key:
        winreg.SetValue(key, "", winreg.REG_SZ, f"URL:{protocol.title()} Protocol")
        winreg.SetValue(key, "URL Protocol", winreg.REG_SZ, "")
        winreg.SetValue(key, r"shell\open\command", winreg.REG_SZ, command)
        if icon:
            winreg.SetValue(key, "DefaultIcon", winreg.REG_SZ, icon)
        if identifier:
            # We add this one value for traceability; not required
            winreg.SetValue(key, "_menuinst", winreg.REG_SZ, identifier)


def unregister_url_protocol(protocol, identifier=None, mode="user"):
    if mode == "system":
        key_tuple = winreg.HKEY_CLASSES_ROOT, protocol
        key_str = fr"HKCR\{protocol}"
    else:
        key_tuple = winreg.HKEY_CURRENT_USER, fr"Software\Classes\{protocol}"
        key_str = fr"HKCU\Software\Classes\{protocol}"
    try:
        with winreg.OpenKey(*key_tuple) as key:
            value, _  = winreg.QueryValueEx(key, "_menuinst")
            delete = identifier is None or value == identifier
    except OSError as exc:
        log.exception("Could not check key %s for deletion", protocol, exc_info=exc)
        return

    if delete:
        _reg_exe("delete", key_str, check=False)
