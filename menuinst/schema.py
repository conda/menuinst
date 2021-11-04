"""
Generate JSON schemas from pydantic models
"""

from typing import Optional, Union
import json
from pathlib import Path

from pydantic import BaseModel as _BaseModel, Field, constr, conlist


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
                "Linux-specific instructions. You can override global keys here if needed"
                terminal: Optional[bool] = Field(
                    False,
                    description="Whether to run the command as part "
                    "of a terminal shell or not.",
                )

            class MacOS(OptionalMenuItemMetadata):
                "Mac-specific instructions. You can override global keys here if needed"

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


if __name__ == "__main__":
    dump_to_json()
