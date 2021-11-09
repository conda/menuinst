"""
Generate JSON schemas from pydantic models
"""

import sys
from typing import Optional, Union, List
import json
from pathlib import Path
from logging import getLogger

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


class OptionalMenuItemMetadata(MenuItemMetadata):
    """Same as MenuItemMetadata, but all is optional. Keep up-to-date!"""

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

                GenericName: Optional[str] = None
                Terminal: Optional[bool] = None
                NoDisplay: Optional[bool] = None
                Hidden: Optional[bool] = None
                OnlyShowIn: Optional[Union[List[str], str]] = None
                NotShowIn: Optional[Union[List[str], str]] = None
                DBusActivatable: Optional[bool] = None
                TryExec: Optional[str] = None
                Terminal: Optional[bool] = None
                MimeType: Optional[Union[List[str], str]] = None
                Categories: Optional[Union[List[str], str]] = None
                Implements: Optional[Union[List[str], str]] = None
                Keywords: Optional[Union[List[str], str]] = None
                StartupNotify: Optional[bool] = None
                StartupWMClass: Optional[str] = None
                PrefersNonDefaultGPU: Optional[bool] = None

            class MacOS(OptionalMenuItemMetadata):
                "Mac-specific instructions. You can override global keys here if needed"

            win: Optional[Windows]
            linux: Optional[Linux]
            osx: Optional[MacOS]

        platforms: Platforms

        def merge_for_platform(self, platform=sys.platform):
            """
            Merge platform keys with global keys, overwriting if needed.
            """
            platform = platform_key(platform)
            global_level = self.dict()
            all_platforms = global_level.pop("platforms", None)
            if all_platforms:
                platform_options = all_platforms.pop(platform)
                if platform_options:
                    for key, value in platform_options.items():
                        if key not in global_level:
                            # bring missing keys, since they are platform specific
                            global_level[key] = value
                        elif value is not None:
                            # if the key was in global, it was not platform specific
                            # this is an override and we only do so if is not None
                            log.debug("Platform value %s=%s overrides global value", key, value)
                            global_level[key] = value

            global_level["platforms"] = [key for key, value in self.platforms if value is not None]

            # this builds an unvalidated model, but we have validated everything already
            # we skip validation because we only want this as a convenient access to values
            # through model.key syntax instead of model["key"]
            return self.construct(**global_level)

        def enabled_for_platform(self, platform=sys.platform):
            platform = platform_key(platform)
            return getattr(self.platforms, platform, None) is not None

    menu_name: constr(min_length=1) = Field(
        description="Name for the category containing the items specified in `menu_items`."
    )
    menu_items: conlist(MenuItem, min_items=1) = Field(
        description="List of menu entries to create across main desktop systems"
    )

    def enabled_for_platform(self, platform=sys.platform):
        return any(item.enabled_for_platform(platform) for item in self.menu_items)


def validate(metadata: Union[str, dict]) -> MenuInstSchema:
    if isinstance(metadata, (str, Path)):
        with open(metadata) as f:
            metadata = json.load(f)

    return MenuInstSchema.validate(metadata)


def dump_to_json():
    here = Path(__file__).parent
    schema = json.dumps(MenuInstSchema.schema(), indent=2)
    print(schema)
    with open(here / "data" / "menuinst.schema.json", "w") as f:
        f.write(schema)


def platform_key(platform=sys.platform):
    if platform == "win32":
        return "win"
    if platform == "darwin":
        return "osx"
    if platform.startswith("linux"):
        return "linux"

    raise ValueError(f"Platform {platform} is not supported")


if __name__ == "__main__":
    dump_to_json()
