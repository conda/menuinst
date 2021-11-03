"""
Generate JSON schemas from pydantic models
"""

from typing import List, Union, Optional, Set
import json
from pathlib import Path

import pydantic
from pydantic import BaseModel as _BaseModel, Field, constr, conlist


class BaseModel(_BaseModel):
    class Config:
        extra = "forbid"


class _AllOptional(pydantic.main.ModelMetaclass):
    """
    Turns all fields optional in a pydantic model
    """

    def __new__(self, name, bases, namespaces, **kwargs):
        if "__annotations__" in namespaces:
            for name, value in namespaces["__annotations__"].copy().items():
                if not name.startswith("__"):
                    namespaces["__annotations__"][name] = Optional[value]
        return super().__new__(self, name, bases, namespaces, **kwargs)


class MenuItemMetadata(BaseModel):
    name: constr(min_length=1) = Field(description="The name of the menu item")
    description: str = Field(
        description="A longer description of the menu item. Shown on popup messages."
    )
    icon: constr(min_length=1) = Field(
        description="Path to the file representing or containing the icon."
    )
    command: conlist(str, min_items=1) = Field(
        description="Command to run with the menu item, expressed as a "
        "list of strings where each string is an argument"
    )
    working_dir: constr(min_length=1) = Field(
        None,
        description="Working directory for the running process. "
        "Defaults to user directory on each platform.",
    )


class OptionalMenuItemMetadata(MenuItemMetadata, metaclass=_AllOptional):
    """Same as MenuItemMetadata, but marked as Optional"""


class MenuInstSchema(BaseModel):
    "Metadata required to create menu items across operating systems with `menuinst`"

    class MenuItem(MenuItemMetadata):
        "Instructions to create a menu item across operating systems."

        class Platforms(BaseModel):
            "Platform specific options. Presence of a platform enables menu items in that platform"

            class Windows(OptionalMenuItemMetadata):
                "Windows-specific instructions. You can override global keys here if needed"
                desktop: bool = Field(
                    True,
                    description="Whether to create a desktop icon in "
                    "addition to the Start Menu item.",
                )
                quicklaunch: bool = Field(
                    True,
                    description="Whether to create a quick launch icon in "
                    "addition to the Start Menu item.",
                )

            class Linux(OptionalMenuItemMetadata):
                "Linux-specific instructions. You can override global keys here if needed"
                terminal: bool = Field(
                    False,
                    description="Whether to run the command as part "
                    "of a terminal shell or not.",
                )

            class MacOS(OptionalMenuItemMetadata):
                "Mac-specific instructions. You can override global keys here if needed"
                pass

            windows: Windows = None
            linux: Linux = None
            osx: MacOS = None

        platforms: Platforms

    menu_name: constr(min_length=1) = Field(
        description="Name for the category containing the items specified in `menu_items`."
    )
    menu_items: conlist(MenuItem, min_items=1) = Field(
        description="List of menu entries to create across main desktop systems"
    )


def main():
    here = Path(__file__).parent
    schema = json.dumps(MenuInstSchema.schema(), indent=2)
    print(schema)
    with open(here / "menuinst.schema.json", "w") as f:
        f.write(schema)


if __name__ == "__main__":
    main()
