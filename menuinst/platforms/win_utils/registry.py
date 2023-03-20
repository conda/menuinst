r"""
Utilities for Windows Registry manipulation

Notes:

winreg.SetValue -> sets _keys_ with default ("") values
winreg.SetValueEx -> sets values with named contents

This is important when the argument has backslashes.
SetValue will process the backslashes into a path of keys
SetValueEx will create a value with name "path\with\keys"


Mnemonic: SetValueEx for "excalars" (scalars, named values)
"""
import winreg
from logging import getLogger
from subprocess import run

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
    """
    We want to achieve this. Entries ending in / denote keys; no trailing / means named value.
    If the item has a value attached to it, it's written after the : symbol.

    HKEY_*/ # current user or local machine
      Software/
        Classes/
          .<extension>/
            OpenWithProgids/
              <extension-handler>
          ...
          <extension-handler>/: "a description of the file being handled"
            DefaultIcon: "path to the app icon"
            shell/
              open/
                command/: "the command to be executed when opening a file with this extension"
    """
    with winreg.OpenKeyEx(
        winreg.HKEY_LOCAL_MACHINE  # HKLM
        if mode == "system"
        else winreg.HKEY_CURRENT_USER,  # HKCU
        r"Software\Classes"
    ) as key:
        # First we associate an extension with a handler
        winreg.SetValueEx(
            winreg.CreateKey(key, fr"{extension}\OpenWithProgids"),
            identifier,
            0,
            winreg.REG_SZ,
            "", # presence of the key is enough
        )
        log.debug("Created registry entry for extension '%s'", extension)

        # Now we register the handler
        handler_desc = f"{extension} {identifier} handler"
        winreg.SetValue(key, identifier, winreg.REG_SZ, handler_desc)
        log.debug("Created registry entry for handler '%s'", identifier)

        # and set the 'open' command
        subkey = rf"{identifier}\shell\open\command"
        # Use SetValue to create subkeys as necessary
        winreg.SetValue(key, subkey, winreg.REG_SZ, command)
        log.debug("Created registry entry for command '%s'", command)

        if icon:
            subkey = winreg.OpenKey(key, identifier)
            winreg.SetValueEx(subkey, "DefaultIcon", 0, winreg.REG_SZ, icon)
            log.debug("Created registry entry for icon '%s'", icon)

        # TODO: We can add contextual menu items too
        # via f"{handler_key}\shell\<Command Title>\command"


def unregister_file_extension(extension, identifier, mode="user"):
    root, root_str = (winreg.HKEY_LOCAL_MACHINE, "HKLM") if mode == "system" else (winreg.HKEY_CURRENT_USER, "HKCU")
    _reg_exe("delete", fr"{root_str}\Software\Classes\{identifier}")

    try:
        with winreg.OpenKey(root, fr"Software\Classes\{extension}\OpenWithProgids", 0, winreg.KEY_ALL_ACCESS) as key:
            try:
                winreg.QueryValueEx(key, identifier)
            except FileNotFoundError:
                log.debug("Handler '%s' is not associated with extension '%s'", identifier, extension)
            else:
                winreg.DeleteValue(key, identifier)
    except Exception as exc:
        log.exception("Could not check key '%s' for deletion", extension, exc_info=exc)
        raise


def register_url_protocol(protocol, command, identifier=None, icon=None, mode="user"):
    if mode == "system":
        key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, protocol)
    else:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, fr"Software\Classes\{protocol}")
    with key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"URL:{protocol.title()}")
        winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
        # SetValue creates sub keys when slashes are present;
        # SetValueEx creates a value with backslashes - we don't want that here
        winreg.SetValue(key, r"shell\open\command", winreg.REG_SZ, command)
        if icon:
            winreg.SetValueEx(key, "DefaultIcon", 0, winreg.REG_SZ, icon)
        if identifier:
            # We add this one value for traceability; not required
            winreg.SetValueEx(key, "_menuinst", 0, winreg.REG_SZ, identifier)


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
