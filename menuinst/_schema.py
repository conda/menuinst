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
    * This needs to be kept up-to-date!
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
    precommand: Optional[str] = Field(
        None,
        description="(Simple, preferrably single-line) logic to run before the command is run. "
        "Runs before the env is activated, if that applies."
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

                Categories: Optional[Union[List[str], constr(regex="^.+;$")]] = None
                DBusActivatable: Optional[bool] = None
                GenericName: Optional[str] = None
                Hidden: Optional[bool] = None
                Implements: Optional[Union[List[str], constr(regex="^.+;$")]] = None
                Keywords: Optional[Union[List[str], constr(regex="^.+;$")]] = None
                MimeType: Optional[Union[List[str], constr(regex="^.+;$")]] = None
                NoDisplay: Optional[bool] = None
                NotShowIn: Optional[Union[List[str], constr(regex="^.+;$")]] = None
                OnlyShowIn: Optional[Union[List[str], constr(regex="^.+;$")]] = None
                PrefersNonDefaultGPU: Optional[bool] = None
                StartupNotify: Optional[bool] = None
                StartupWMClass: Optional[str] = None
                TryExec: Optional[str] = None

            class MacOS(OptionalMenuItemMetadata):
                """Mac-specific instructions. Check theseURL for more info:
                - CF* keys: https://developer.apple.com/library/archive/documentation/General/Reference/InfoPlistKeyReference/Articles/CoreFoundationKeys.html
                - LS* keys: https://developer.apple.com/library/archive/documentation/General/Reference/InfoPlistKeyReference/Articles/LaunchServicesKeys.html
                - entitlements: list those which should be true for the shortcut signing
                  See https://developer.apple.com/documentation/bundleresources/entitlements.
                  
                You can also override global keys here if needed.
                """

                class _CFBundleURLTypes(BaseModel):
                    CFBundleTypeRole: str
                    CFBundleURLSchemes: List[str]
                    CFBundleURLName: Optional[str] = None
                    CFBundleURLIconFile: Optional[str] = None

                class _CFBundleDocumentTypes(BaseModel):
                    CFBundleTypeIconFile: constr(regex=r"^.+\.icns$")
                    CFBundleTypeName: str
                    CFBundleTypeRole: Union[Literal["Editor"], Literal["Viewer"], Literal["Shell"], Literal["None"]]
                    LSItemContentTypes: List[str]
                    LSHandlerRank: Union[Literal["Owner"], Literal["Default"], Literal["Alternate"]]

                CFBundleDisplayName: Optional[str] = None
                CFBundleIdentifier: Optional[str] = None
                CFBundleName: Optional[str] = None
                CFBundleSpokenName: Optional[str] = None
                CFBundleVersion: Optional[constr(regex=r"^\S+$")] = None
                CFBundleURLTypes: Optional[_CFBundleURLTypes] = None
                CFBundleDocumentTypes: Optional[_CFBundleDocumentTypes] = None
                LSApplicationCategoryType: Optional[constr(regex=r"^public\.app-category\.\S+$")]
                LSBackgroundOnly: Optional[bool] = None
                LSEnvironment: Optional[Dict[str, str]] = None
                LSMinimumSystemVersion: Optional[constr(regex=r"^\d+\.\d+\.\d+$")] = None
                LSMultipleInstancesProhibited: Optional[bool] = None
                entitlements: Optional[List[constr(regex=r"[a-z0-9\.\-]+")]] = None

            win: Optional[Windows]
            linux: Optional[Linux]
            osx: Optional[MacOS]

        platforms: Platforms

    menu_name: constr(min_length=1) = Field(
        description="Name for the category containing the items specified in `menu_items`."
    )
    menu_items: conlist(MenuItem, min_items=1) = Field(
        description="List of menu entries to create across main desktop systems"
    )

    id_: Literal["https://schemas.conda.io/menuinst-1.schema.json"] = Field(
        description="Version of the menuinst schema",
        alias="$id",
    )

    schema_: Literal["https://json-schema.org/draft-07/schema"] = Field(
        description="Standard of the JSON schema we adhere to",
        alias="$schema",
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
