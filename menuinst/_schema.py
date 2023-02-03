"""
Generate JSON schemas from pydantic models
"""

from pprint import pprint
from typing import Optional, Union, List, Literal, Dict
from pathlib import Path
from logging import getLogger
import json

from pydantic import BaseModel as _BaseModel, Field, constr, conlist

log = getLogger(__name__)


class BaseModel(_BaseModel):
    class Config:
        extra = "forbid"


class MenuItemMetadata(BaseModel):
    name: constr(min_length=1) = Field(..., description="The name of the menu item")
    description: str = Field(
        ..., description="A longer description of the menu item. Shown on popup messages."
    )
    icon: constr(min_length=1) = Field(
        None, description="Path to the file representing or containing the icon."
    )
    precommand: constr(min_length=1) = Field(
        None,
        description="(Simple, preferrably single-line) logic to run before the command is run. "
        "Runs before the env is activated, if that applies."
    )
    precreate: constr(min_length=1) = Field(
        None,
        description="(Simple, preferrably single-line) logic to run before the shortcut is created."
    )
    command: conlist(str, min_items=1) = Field(
        ...,
        description="Command to run with the menu item, expressed as a "
        "list of strings where each string is an argument",
    )
    working_dir: constr(min_length=1) = Field(
        None,
        description="Working directory for the running process. "
        "Defaults to user directory on each platform.",
    )
    activate: bool = Field(
        True,
        description="Whether to activate the target environment before running `command`.",
    )
    terminal: bool = Field(
        False,
        description="Whether run the program in a terminal/console or not. "
        "On Windows, it only has an effect if activate is true. "
        "On MacOS, arguments are ignored.",
    )


class OptionalMenuItemMetadata(MenuItemMetadata):
    """
    Same as MenuItemMetadata, but all is optional.

    Note:
    * This needs to be kept up-to-date with MenuItemMetadata!
    * Default value is always None.
    """

    name: Optional[constr(min_length=1)] = Field(None, description="The name of the menu item")
    description: Optional[str] = Field(
        None, description="A longer description of the menu item. Shown on popup messages."
    )
    icon: Optional[constr(min_length=1)] = Field(
        None, description="Path to the file representing or containing the icon."
    )
    command: Optional[conlist(str, min_items=1)] = Field(
        None,
        description="Command to run with the menu item, expressed as a "
        "list of strings where each string is an argument",
    )
    working_dir: Optional[constr(min_length=1)] = Field(
        None,
        description="Working directory for the running process. "
        "Defaults to user directory on each platform.",
    )
    precommand: Optional[constr(min_length=1)] = Field(
        None,
        description="(Simple, preferrably single-line) logic to run before the command is run. "
        "Runs before the env is activated, if that applies."
    )
    precreate: Optional[constr(min_length=1)] = Field(
        None,
        description="(Simple, preferrably single-line) logic to run before the shortcut is created."
    )
    activate: Optional[bool] = Field(
        None,
        description="Whether to activate the target environment before running `command`.",
    )
    terminal: Optional[bool] = Field(
        None,
        description="Whether run the program in a terminal/console or not. "
        "On Windows, it only has an effect if activate is true. "
        "On MacOS, arguments are ignored.",
    )



class MenuInstSchema(BaseModel):
    "Metadata required to create menu items across operating systems with `menuinst`"

    class MenuItem(MenuItemMetadata):
        "Instructions to create a menu item across operating systems."

        class Platforms(BaseModel):
            "Platform specific options. Presence of a platform enables menu items in that platform"

            class Windows(OptionalMenuItemMetadata):
                "Windows-specific instructions. You can override global keys here if needed"

                desktop: Optional[bool] = Field(
                    True,
                    description="Whether to create a desktop icon in "
                    "addition to the Start Menu item.",
                )
                quicklaunch: Optional[bool] = Field(
                    True,
                    description="Whether to create a quick launch icon in "
                    "addition to the Start Menu item.",
                )

            class Linux(OptionalMenuItemMetadata):
                """Linux-specific instructions. Check
                https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html#recognized-keys
                for more information. You can override global keys here if needed"""

                Categories: Optional[Union[List[str], constr(regex=r"^.+;$")]] = Field(
                    None,
                    description="Categories in which the entry should be shown in a menu. "
                    "See 'Registered categories' in "
                    "http://www.freedesktop.org/Standards/menu-spec.",
                )
                DBusActivatable: Optional[bool] = Field(
                    None,
                    description="A boolean value specifying if D-Bus activation "
                    "is supported for this application.",
                )
                GenericName: Optional[str] = Field(
                    None,
                    description="Generic name of the application; e.g. if the name is 'conda', "
                    "this would be 'Package Manager'.",
                )
                Hidden: Optional[bool] = Field(
                    None,
                    description="Disable shortcut, signaling a missing resource.",
                )
                Implements: Optional[Union[List[str], constr(regex=r"^.+;$")]] = Field(
                    None,
                    description="List of supported interfaces. See "
                    "https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html#interfaces",
                )
                Keywords: Optional[Union[List[str], constr(regex=r"^.+;$")]] = Field(
                    None,
                    description="Additional terms to describe this shortcut to aid in searching.",
                )
                MimeType: Optional[Union[List[str], constr(regex=r"^.+;$")]] = Field(
                    None,
                    description="The MIME type(s) supported by this application.",
                )
                NoDisplay: Optional[bool] = Field(
                    None,
                    description="Do not show this item in the menu. Useful to associate MIME types "
                    "and other registrations, without having an actual clickable item. Not to be "
                    "confused with 'Hidden'.",
                )
                NotShowIn: Optional[Union[List[str], constr(regex=r"^.+;$")]] = Field(
                    None,
                    description="Desktop environments that should NOT display this item. "
                    "It'll check against $XDG_CURRENT_DESKTOP.",
                )
                OnlyShowIn: Optional[Union[List[str], constr(regex=r"^.+;$")]] = Field(
                    None,
                    description="Desktop environments that should display this item. "
                    "It'll check against $XDG_CURRENT_DESKTOP.",
                )
                PrefersNonDefaultGPU: Optional[bool] = Field(
                    None,
                    description="Hint that the app prefers to be run on a more powerful discrete "
                    "GPU if available",
                )
                StartupNotify: Optional[bool] = Field(
                    None,
                    description="Advanced. See "
                    "https://www.freedesktop.org/wiki/Specifications/startup-notification-spec/",
                )
                StartupWMClass: Optional[str] = Field(
                    None,
                    description="Advanced. See "
                    "https://www.freedesktop.org/wiki/Specifications/startup-notification-spec/",
                )
                TryExec: Optional[str] = Field(
                    None,
                    description="Filename or absolute path to an executable file on disk used to "
                    "determine if the program is actually installed and can be run. If the test "
                    "fails, the shortcut might be ignored / hidden.",
                )

            class MacOS(OptionalMenuItemMetadata):
                """
                Mac-specific instructions. Check these URLs for more info:

                - ``CF*`` keys: see `Core Foundation Keys <cf-keys>`_
                - ``LS*`` keys: see `Launch Services Keys <ls-keys>`_
                - ``entitlements``: list those which should be true for the shortcut signing;
                  see `entitlements docs <entitlements>`_
                
                You can also override global keys here if needed

                .. _cf-keys: https://developer.apple.com/library/archive/documentation/General/Reference/InfoPlistKeyReference/Articles/CoreFoundationKeys.html
                .. _ls-keys: https://developer.apple.com/library/archive/documentation/General/Reference/InfoPlistKeyReference/Articles/LaunchServicesKeys.html
                .. _entitlements: https://developer.apple.com/documentation/bundleresources/entitlements.
                """

                class CFBundleURLTypesModel(BaseModel):
                    "Describes a URL scheme associated with the app."
                    CFBundleTypeRole: Literal["Editor", "Viewer", "Shell", "None"] = Field(
                        ...,
                        description="This key specifies the app's role with respect to the URL."
                    )
                    CFBundleURLSchemes: List[str] = Field(
                        ...,
                        description="URL schemes / protocols handled by this type (e.g. 'mailto').",
                    )
                    CFBundleURLName: Optional[str] = Field(
                        None,
                        description="Abstract name for this URL type. Uniqueness recommended.",
                    )
                    CFBundleURLIconFile: Optional[str] = Field(
                        None,
                        description="Name of the icon image file (minus the .icns extension).",
                    )

                class CFBundleDocumentTypesModel(BaseModel):
                    "Describes a document type associated with the app."
                    CFBundleTypeIconFile: Optional[str] = Field(
                        None,
                        description="Name of the icon image file (minus the .icns extension).",
                    )
                    CFBundleTypeName: str = Field(
                        ...,
                        description="Abstract name for this document type. Uniqueness recommended.",
                    )
                    CFBundleTypeRole: Literal["Editor", "Viewer", "Shell", "None"] = Field(
                        ...,
                        description="This key specifies the app's role with respect to the type."
                    )
                    LSItemContentTypes: List[str] = Field(
                        ...,
                        description="List of UTI strings defining a supported file type; e.g. for "
                        "PNG files, use 'public.png'. Sync with 'NSExportableTypes' key with the "
                        "appropriate entries"
                    )
                    LSHandlerRank: Literal["Owner", "Default", "Alternate"] = Field(
                        ...,
                        description="Determines how Launch Services ranks this app among the apps "
                        "that declare themselves editors or viewers of files of this type."
                    )

                CFBundleDisplayName: Optional[str] = Field(
                    None,
                    description="Display name of the bundle, visible to users and used by Siri. If "
                    "not provided, 'menuinst' will use the 'name' field.",
                )
                CFBundleIdentifier: Optional[str] = Field(
                    None,
                    description="",
                )
                CFBundleName: Optional[constr(max_length=16)] = Field(
                    None,
                    description="Short name of the bundle. Maybe used if 'CFBundleDisplayName' is "
                    "absent. If not provided, 'menuinst' will generate one from the 'name' field.",
                )
                CFBundleSpokenName: Optional[str] = Field(
                    None,
                    description="Suitable replacement for text-to-speech operations on the app "
                    "For example, 'my app one two three' instead of 'MyApp123'.",
                )
                CFBundleVersion: Optional[constr(regex=r"^\S+$")] = Field(
                    None,
                    description="Build version number for the bundle. In the context of 'menuinst' "
                    "this can be used to signal a new version of the menu item for the same "
                    "application version.",
                )
                CFBundleURLTypes: Optional[List[CFBundleURLTypesModel]] = Field(
                    None,
                    description="URL types supported by this app.",
                )
                CFBundleDocumentTypes: Optional[List[CFBundleDocumentTypesModel]] = Field(
                    None,
                    description="Document types supported by this app.",
                )
                LSApplicationCategoryType: Optional[constr(regex=r"^public\.app-category\.\S+$")] = Field(
                    None,
                    description="The App Store uses this string to determine the appropriate "
                    "categorization for the app",
                )
                LSBackgroundOnly: Optional[bool] = Field(
                    None,
                    description="Specifies whether this app runs only in the background.",
                )
                LSEnvironment: Optional[Dict[str, str]] = Field(
                    None,
                    description="List of key-value pairs used to define environment variables.",
                )
                LSMinimumSystemVersion: Optional[constr(regex=r"^\d+\.\d+\.\d+$")] = Field(
                    None,
                    description="Minimum version of macOS required for this app to run, as x.y.z. "
                    "For example, for macOS v10.4 and later, use '10.4.0'.",
                )
                LSMultipleInstancesProhibited: Optional[bool] = Field(
                    None,
                    description="Whether an app is prohibited from running simultaneously in "
                    "multiple user sessions",
                )
                LSRequiresNativeExecution: Optional[bool] = Field(
                    None,
                    description="If true, prevent a universal binary from being run under Rosetta "
                    "emulation on an Intel-based Mac",
                )
                entitlements: Optional[List[constr(regex=r"[a-z0-9\.\-]+")]] = Field(
                    None,
                    description="List of permissions to request for the launched application. "
                    "See https://developer.apple.com/documentation/bundleresources/entitlements "
                    "for a full list of possible values.",
                )
                link_in_bundle: Optional[Dict[constr(min_length=1), constr(regex=r"^(?!\/)(?!\.\./).*")]] = Field(
                    None,
                    description="Paths that should be symlinked into the shortcut app bundle. "
                    "It takes a mapping of source to destination paths. Destination paths must be "
                    "relative. Placeholder ``{{ MENU_ITEM_LOCATION }}`` can be useful.",
                )

            win: Optional[Windows]
            "Options for Windows. See :class:`Windows` model for details."
            linux: Optional[Linux]
            "Options for Linux. See :class:`Linux` model for details."
            osx: Optional[MacOS]
            "Options for macOS. See :class:`MacOS` model for details."

        platforms: Platforms
        "Platform-specific options"

    id_: Literal["https://schemas.conda.io/menuinst-1.schema.json"] = Field(
        description="Version of the menuinst schema.",
        alias="$id",
    )
    schema_: Literal["https://json-schema.org/draft-07/schema"] = Field(
        description="Standard of the JSON schema we adhere to.",
        alias="$schema",
    )
    menu_name: constr(min_length=1) = Field(
        description="Name for the category containing the items specified in ``menu_items``."
    )
    menu_items: conlist(MenuItem, min_items=1) = Field(
        description="List of menu entries to create across main desktop systems."
    )


def dump_schema_to_json(write=True):
    if write:
        here = Path(__file__).parent
        schema = MenuInstSchema.schema_json(indent=2)
        print(schema)
        with open(here / "data" / "menuinst.schema.json", "w") as f:
            f.write(schema)
    return MenuInstSchema.schema()


def dump_default_to_json(write=True):
    here = Path(__file__).parent
    default = MenuInstSchema.MenuItem(
        name="Default",
        description="",
        command=["replace", "this"],
        platforms={}
    ).dict()
    def platform_default(platform):
        return {
            k: v
            for k, v in getattr(MenuInstSchema.MenuItem.Platforms, platform)().dict().items()
            if k not in MenuInstSchema.MenuItem.__fields__
        }
    default["platforms"] = {
        "win": platform_default("Windows"),
        "osx": platform_default("MacOS"),
        "linux": platform_default("Linux"),
    }
    if write:
        pprint(default)
        with open(here / "data" / "menuinst.menu_item.default.json", "w") as f:
            json.dump(default, f, indent=2)
    return default


def validate(metadata_or_path):
    if isinstance(metadata_or_path, (str, Path)):
        with open(metadata_or_path) as f:
            metadata = json.load(f)
    else:
        metadata = metadata_or_path
    return MenuInstSchema(**metadata)


if __name__ == "__main__":
    dump_schema_to_json()
    dump_default_to_json()
