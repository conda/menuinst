"""
Generate JSON schemas from pydantic models
"""

# flake8: noqa
# pyright: reportInvalidTypeForm=false, reportCallIssue=false, reportGeneralTypeIssues=false

import json
import os
import re
from inspect import cleandoc
from logging import getLogger
from pathlib import Path
from pprint import pprint
from typing import Dict, List, Literal, Optional, Union

try:
    from pydantic.v1 import BaseModel as _BaseModel
    from pydantic.v1 import Field as _Field
    from pydantic.v1 import conlist, constr
except ImportError:
    # pydantic v1
    from pydantic import BaseModel as _BaseModel
    from pydantic import Field as _Field
    from pydantic import conlist, constr


log = getLogger(__name__)


def _clean_description(description: str) -> str:
    # The regex below only replaces newlines surrounded by non-newlines
    description = re.sub(r'(?<!\n)\n(?=\S)', ' ', cleandoc(description))
    if os.environ.get("SPHINX_RUNNING"):
        # We need this for autodoc-pydantic compatibility, which expects RST
        import commonmark

        ast = commonmark.Parser().parse(description)
        description = commonmark.ReStructuredTextRenderer().render(ast)
    return description


class BaseModel(_BaseModel):
    class Config:
        extra = "forbid"

        @staticmethod
        def schema_extra(schema, model):
            if description := schema.get("description"):
                description = _clean_description(description)
                schema["description"] = description
                schema["markdownDescription"] = description


def Field(*args, **kwargs):
    if description := kwargs.get("description"):
        kwargs["description"] = kwargs["markdownDescription"] = _clean_description(description)
    return _Field(*args, **kwargs)


class MenuItemNameDict(BaseModel):
    """
    Variable menu item name.
    Use this dictionary if the menu item name depends on installation parameters
    such as the target environment.
    """

    target_environment_is_base: Optional[constr(min_length=1)] = Field(
        None,
        description=("Name when target environment is the base environment."),
    )
    target_environment_is_not_base: Optional[constr(min_length=1)] = Field(
        None,
        description=("Name when target environment is not the base environment."),
    )


class BasePlatformSpecific(BaseModel):
    """
    Same as `MenuItem`, but without `platforms`, and all is optional.

    Note:
    * This needs to be kept up-to-date with `MenuItem`!
    * Default value is always `None`.
    """

    name: Optional[Union[constr(min_length=1), MenuItemNameDict]] = Field(
        None,
        description=(
            """
            The name of the menu item. Can be a dictionary if the name depends on
            installation parameters. See `MenuItemNameDict` for details.
            """
        ),
    )
    description: Optional[str] = Field(
        None,
        description=("A longer description of the menu item. Shown on popup messages."),
    )
    icon: Optional[constr(min_length=1)] = Field(
        None,
        description=("Path to the file representing or containing the icon."),
    )
    command: Optional[conlist(str, min_items=1)] = Field(
        None,
        description=(
            """
            Command to run with the menu item, expressed as a
            list of strings where each string is an argument.
            """
        ),
    )
    working_dir: Optional[constr(min_length=1)] = Field(
        None,
        description=(
            """
            Working directory for the running process.
            Defaults to user directory on each platform.
            """
        ),
    )
    precommand: Optional[constr(min_length=1)] = Field(
        None,
        description=(
            """
            (Simple, preferrably single-line) logic to run before the command is run.
            Runs before the environment is activated, if that applies.
            """
        ),
    )
    precreate: Optional[constr(min_length=1)] = Field(
        None,
        description=(
            """(Simple, preferrably single-line) logic to run before the shortcut is created."""
        ),
    )
    activate: Optional[bool] = Field(
        None,
        description=("Whether to activate the target environment before running `command`."),
    )
    terminal: Optional[bool] = Field(
        None,
        description=(
            """
            Whether run the program in a terminal/console or not.
            On Windows, it only has an effect if `activate` is true.
            On MacOS, the application will ignore command-line arguments.
            """
        ),
    )


class Windows(BasePlatformSpecific):
    "Windows-specific instructions. You can override global keys here if needed"

    desktop: Optional[bool] = Field(
        True,
        description=("Whether to create a desktop icon in addition to the Start Menu item."),
    )
    quicklaunch: Optional[bool] = Field(
        False,
        description=(
            """
            DEPRECATED. Whether to create a quick launch icon in addition to the Start Menu item.
            """
        ),
        deprecated=True,
    )
    terminal_profile: constr(min_length=1) = Field(
        None,
        description=(
            """
            Name of the Windows Terminal profile to create.
            This name must be unique across multiple installations because
            menuinst will overwrite Terminal profiles with the same name.
            """
        ),
    )
    url_protocols: Optional[List[constr(regex=r"\S+")]] = Field(
        None,
        description=("URL protocols that will be associated with this program."),
    )
    file_extensions: Optional[List[constr(regex=r"\.\S*")]] = Field(
        None,
        description=("File extensions that will be associated with this program."),
    )
    app_user_model_id: Optional[constr(regex=r"\S+\.\S+", max_length=128)] = Field(
        None,
        description=(
            """
            Identifier used in Windows 7 and above to associate processes, files and windows with a
            particular application. If your shortcut produces duplicated icons, you need to define
            this field. If not set, it will default to `Menuinst.<name>`.

            See [AppUserModelID docs](
            https://learn.microsoft.com/en-us/windows/win32/shell/appids#how-to-form-an-application-defined-appusermodelid)
            for more information on the required string format.
            """
        ),
    )


class Linux(BasePlatformSpecific):
    """
    Linux-specific instructions.

    Check the [Desktop entry specification](
    https://specifications.freedesktop.org/desktop-entry-spec/latest/recognized-keys.html)
    for more details.
    """

    Categories: Optional[Union[List[str], constr(regex=r"^.+;$")]] = Field(
        None,
        description=(
            """
            Categories in which the entry should be shown in a menu.
            See 'Registered categories' in the [Menu Spec](
            http://www.freedesktop.org/Standards/menu-spec).
            """
        ),
    )
    DBusActivatable: Optional[bool] = Field(
        None,
        description=(
            """
            A boolean value specifying if D-Bus activation is supported for this application.
            """
        ),
    )
    GenericName: Optional[str] = Field(
        None,
        description=(
            """
            Generic name of the application; e.g. if the name is 'conda',
            this would be 'Package Manager'.
            """
        ),
    )
    Hidden: Optional[bool] = Field(
        None,
        description=("Disable shortcut, signaling a missing resource."),
    )
    Implements: Optional[Union[List[str], constr(regex=r"^.+;$")]] = Field(
        None,
        description=(
            """
            List of supported interfaces. See 'Interfaces' in [Desktop Entry Spec](
            https://specifications.freedesktop.org/desktop-entry-spec/latest/interfaces.html).
            """
        ),
    )
    Keywords: Optional[Union[List[str], constr(regex=r"^.+;$")]] = Field(
        None,
        description=("Additional terms to describe this shortcut to aid in searching."),
    )
    MimeType: Optional[Union[List[str], constr(regex=r"^.+;$")]] = Field(
        None,
        description=(
            """
            The MIME type(s) supported by this application.
            Note this includes file types and URL protocols.
            For URL protocols, use `x-scheme-handler/your-protocol-here`.
            For example, if you want to register `menuinst:`, you would
            include `x-scheme-handler/menuinst`.
            """
        ),
    )
    NoDisplay: Optional[bool] = Field(
        None,
        description=(
            """
            Do not show this item in the menu. Useful to associate MIME types
            and other registrations, without having an actual clickable item.
            Not to be confused with 'Hidden'.
            """
        ),
    )
    NotShowIn: Optional[Union[List[str], constr(regex=r"^.+;$")]] = Field(
        None,
        description=(
            """
            Desktop environments that should NOT display this item.
            It'll check against `$XDG_CURRENT_DESKTOP`.
            """
        ),
    )
    OnlyShowIn: Optional[Union[List[str], constr(regex=r"^.+;$")]] = Field(
        None,
        description=(
            """
            Desktop environments that should display this item.
            It'll check against `$XDG_CURRENT_DESKTOP`.
            """
        ),
    )
    PrefersNonDefaultGPU: Optional[bool] = Field(
        None,
        description=(
            """
            Hint that the app prefers to be run on a more powerful discrete GPU if available.
            """
        ),
    )
    SingleMainWindow: Optional[bool] = Field(
        None,
        description=(
            """
            Do not show the 'New Window' option in the app's context menu.
            """
        ),
    )
    StartupNotify: Optional[bool] = Field(
        None,
        description=(
            """
            Advanced. See [Startup Notification spec](
            https://www.freedesktop.org/wiki/Specifications/startup-notification-spec/).
            """
        ),
    )
    StartupWMClass: Optional[str] = Field(
        None,
        description=(
            """
            Advanced. See [Startup Notification spec](
            https://www.freedesktop.org/wiki/Specifications/startup-notification-spec/).
            """
        ),
    )
    TryExec: Optional[str] = Field(
        None,
        description=(
            """
            Filename or absolute path to an executable file on disk used to
            determine if the program is actually installed and can be run. If the test
            fails, the shortcut might be ignored / hidden.
            """
        ),
    )
    glob_patterns: Optional[Dict[str, constr(regex=r".*\*.*")]] = Field(
        None,
        description=(
            """
            Map of custom MIME types to their corresponding glob patterns (e.g. `*.txt`).
            Only needed if you define custom MIME types in `MimeType`.
            """
        ),
    )


class MacOS(BasePlatformSpecific):
    """
    Mac-specific instructions. Check these URLs for more info:

    - `CF*` keys: see [Core Foundation Keys](https://developer.apple.com/library/archive/documentation/General/Reference/InfoPlistKeyReference/Articles/CoreFoundationKeys.html)
    - `LS*` keys: see [Launch Services Keys](https://developer.apple.com/library/archive/documentation/General/Reference/InfoPlistKeyReference/Articles/LaunchServicesKeys.html)
    - `entitlements`: see [Entitlements documentation](https://developer.apple.com/documentation/bundleresources/entitlements)
    """

    class CFBundleURLTypesModel(BaseModel):
        "Describes a URL scheme associated with the app."

        CFBundleTypeRole: Optional[Literal["Editor", "Viewer", "Shell", "None"]] = Field(
            None,
            description=("This key specifies the app's role with respect to the URL."),
        )
        CFBundleURLSchemes: List[str] = Field(
            ...,
            description=("URL schemes / protocols handled by this type (e.g. 'mailto')."),
        )
        CFBundleURLName: Optional[str] = Field(
            None,
            description=("Abstract name for this URL type. Uniqueness recommended."),
        )
        CFBundleURLIconFile: Optional[str] = Field(
            None,
            description=("Name of the icon image file (minus the .icns extension)."),
        )

    class CFBundleDocumentTypesModel(BaseModel):
        "Describes a document type associated with the app."

        CFBundleTypeIconFile: Optional[str] = Field(
            None,
            description=("Name of the icon image file (minus the .icns extension)."),
        )
        CFBundleTypeName: str = Field(
            ...,
            description=("Abstract name for this document type. Uniqueness recommended."),
        )
        CFBundleTypeRole: Optional[Literal["Editor", "Viewer", "Shell", "None"]] = Field(
            None, description=("This key specifies the app's role with respect to the type.")
        )
        LSItemContentTypes: List[str] = Field(
            ...,
            description=(
                """
                List of UTI strings defining a supported file type; e.g. for PNG files, use
                'public.png'. See [UTI Reference](
                https://developer.apple.com/library/archive/documentation/Miscellaneous/Reference/UTIRef/Articles/System-DeclaredUniformTypeIdentifiers.html)
                for more info about the system-defined UTIs. Custom UTIs can be defined via
                'UTExportedTypeDeclarations'. UTIs defined by other apps (not the system) need to
                be imported via 'UTImportedTypeDeclarations'.

                See [Fun with UTIs](https://www.cocoanetics.com/2012/09/fun-with-uti/) for more
                info.
                """
            ),
        )
        LSHandlerRank: Literal["Owner", "Default", "Alternate"] = Field(
            ...,
            description=(
                """
                Determines how Launch Services ranks this app among the apps
                that declare themselves editors or viewers of files of this type.
                """
            ),
        )

    class UTTypeDeclarationModel(BaseModel):
        UTTypeConformsTo: List[str] = Field(
            ...,
            description=("The Uniform Type Identifier types that this type conforms to."),
        )
        UTTypeDescription: Optional[str] = Field(
            None,
            description=("A description for this type."),
        )
        UTTypeIconFile: Optional[str] = Field(
            None,
            description=("The bundle icon resource to associate with this type."),
        )
        UTTypeIdentifier: str = Field(
            ...,
            description=("The Uniform Type Identifier to assign to this type."),
        )
        UTTypeReferenceURL: Optional[str] = Field(
            None,
            description=("The webpage for a reference document that describes this type."),
        )
        UTTypeTagSpecification: Dict[str, List[str]] = Field(
            ...,
            description=("A dictionary defining one or more equivalent type identifiers."),
        )

    CFBundleDisplayName: Optional[str] = Field(
        None,
        description=(
            """
            Display name of the bundle, visible to users and used by Siri. If
            not provided, 'menuinst' will use the 'name' field.
            """
        ),
    )
    CFBundleIdentifier: Optional[constr(regex=r"^[A-z0-9\-\.]+$")] = Field(
        None,
        description=(
            """
            Unique identifier for the shortcut. Typically uses a reverse-DNS format.
            If not provided, 'menuinst' will generate one from the 'name' field.
            """
        ),
    )
    CFBundleName: Optional[constr(max_length=16)] = Field(
        None,
        description=(
            """
            Short name of the bundle. May be used if `CFBundleDisplayName` is
            absent. If not provided, 'menuinst' will generate one from the 'name' field.
            """
        ),
    )
    CFBundleSpokenName: Optional[str] = Field(
        None,
        description=(
            """
            Suitable replacement for text-to-speech operations on the app.
            For example, 'my app one two three' instead of 'MyApp123'.
            """
        ),
    )
    CFBundleVersion: Optional[constr(regex=r"^\S+$")] = Field(
        None,
        description=(
            """
            Build version number for the bundle. In the context of 'menuinst'
            this can be used to signal a new version of the menu item for the same
            application version.
            """
        ),
    )
    CFBundleURLTypes: Optional[List[CFBundleURLTypesModel]] = Field(
        None,
        description=(
            """
            URL types supported by this app. Requires setting `event_handler` too.
            Note this feature requires macOS 10.14.4 or above.
            """
        ),
    )
    CFBundleDocumentTypes: Optional[List[CFBundleDocumentTypesModel]] = Field(
        None,
        description=(
            """
            Document types supported by this app. Requires setting `event_handler` too.
            Requires macOS 10.14.4 or above.
            """
        ),
    )
    LSApplicationCategoryType: Optional[constr(regex=r"^public\.app-category\.\S+$")] = Field(
        None,
        description=(
            "The App Store uses this string to determine the appropriate categorization."
        ),
    )
    LSBackgroundOnly: Optional[bool] = Field(
        None,
        description=("Specifies whether this app runs only in the background."),
    )
    LSEnvironment: Optional[Dict[str, str]] = Field(
        None,
        description=("List of key-value pairs used to define environment variables."),
    )
    LSMinimumSystemVersion: Optional[constr(regex=r"^\d+\.\d+\.\d+$")] = Field(
        None,
        description=(
            """
            Minimum version of macOS required for this app to run, as `x.y.z`.
            For example, for macOS v10.4 and later, use `10.4.0`.
            """
        ),
    )
    LSMultipleInstancesProhibited: Optional[bool] = Field(
        None,
        description=(
            """
            Whether an app is prohibited from running simultaneously in multiple user sessions.
            """
        ),
    )
    LSRequiresNativeExecution: Optional[bool] = Field(
        None,
        description=(
            """
            If true, prevent a universal binary from being run under
            Rosetta emulation on an Intel-based Mac.
            """
        ),
    )
    NSSupportsAutomaticGraphicsSwitching: Optional[bool] = Field(
        None,
        description=("If true, allows an OpenGL app to utilize the integrated GPU."),
    )
    UTExportedTypeDeclarations: Optional[List[UTTypeDeclarationModel]] = Field(
        None,
        description=("The uniform type identifiers owned and exported by the app."),
    )
    UTImportedTypeDeclarations: Optional[List[UTTypeDeclarationModel]] = Field(
        None,
        description=(
            "The uniform type identifiers inherently supported, but not owned, by the app."
        ),
    )
    entitlements: Optional[List[constr(regex=r"[a-z0-9\.\-]+")]] = Field(
        None,
        description=(
            """
            List of permissions to request for the launched application. See [the entitlements docs](
            https://developer.apple.com/documentation/bundleresources/entitlements) for a full
            list of possible values.
            """
        ),
    )
    link_in_bundle: Optional[Dict[constr(min_length=1), constr(regex=r"^(?!\/)(?!\.\./).*")]] = (
        Field(
            None,
            description=(
                """
                Paths that should be symlinked into the shortcut app bundle.
                It takes a mapping of source to destination paths. Destination paths must be
                relative. Placeholder `{{ MENU_ITEM_LOCATION }}` can be useful.
                """
            ),
        )
    )
    event_handler: Optional[constr(min_length=1)] = Field(
        None,
        description=(
            """
            Required shell script logic to handle opened URL payloads.
            Note this feature requires macOS 10.14.4 or above.
            """
        ),
    )


class Platforms(BaseModel):
    """
    Platform specific options.

    Note each of these fields supports the same keys as the top-level `MenuItem`
    (sans `platforms` itself), in case overrides are needed.
    """

    linux: Optional[Linux] = Field(
        description=("Options for Linux. See `Linux` model for details."),
    )
    osx: Optional[MacOS] = Field(
        description=("Options for macOS. See `MacOS` model for details."),
    )
    win: Optional[Windows] = Field(
        description=("Options for Windows. See `Windows` model for details."),
    )


class MenuItem(BaseModel):
    "Instructions to create a menu item across operating systems."

    name: Union[constr(min_length=1), MenuItemNameDict] = Field(
        ...,
        description=(
            """
            The name of the menu item. Can be a dictionary if the name depends on
            installation parameters. See `MenuItemNameDict` for details.
            """
        ),
    )
    description: str = Field(
        ...,
        description=("A longer description of the menu item. Shown on popup messages."),
    )
    command: conlist(str, min_items=1) = Field(
        ...,
        description=(
            """
            Command to run with the menu item, expressed as a
            list of strings where each string is an argument.
            """
        ),
    )
    icon: Optional[constr(min_length=1)] = Field(
        None,
        description=("Path to the file representing or containing the icon."),
    )
    precommand: Optional[constr(min_length=1)] = Field(
        None,
        description=(
            """
            (Simple, preferrably single-line) logic to run before the command is run.
            Runs before the environment is activated, if that applies.
            """
        ),
    )
    precreate: Optional[constr(min_length=1)] = Field(
        None,
        description=(
            """
            (Simple, preferrably single-line) logic to run before the shortcut is created.
            """
        ),
    )
    working_dir: Optional[constr(min_length=1)] = Field(
        None,
        description=(
            """
            Working directory for the running process.
            Defaults to user directory on each platform.
            """
        ),
    )
    activate: Optional[bool] = Field(
        True,
        description=("Whether to activate the target environment before running `command`."),
    )
    terminal: Optional[bool] = Field(
        False,
        description=(
            """
            Whether run the program in a terminal/console or not.
            On Windows, it only has an effect if `activate` is true.
            On MacOS, the application will ignore command-line arguments.
            """
        ),
    )
    platforms: Platforms = Field(
        description=(
            """
            Platform-specific options. Presence of a platform field enables
            menu items in that platform.
            """
        ),
    )


class MenuInstSchema(BaseModel):
    "Metadata required to create menu items across operating systems with `menuinst`."

    id_: Literal["https://schemas.conda.io/menuinst-1.schema.json"] = Field(
        ...,
        description=("Version of the menuinst schema."),
        alias="$id",
    )
    schema_: Literal["https://json-schema.org/draft-07/schema"] = Field(
        ...,
        description=("Standard of the JSON schema we adhere to."),
        alias="$schema",
    )
    menu_name: constr(min_length=1) = Field(
        ...,
        description=("Name for the category containing the items specified in `menu_items`."),
    )
    menu_items: conlist(MenuItem, min_items=1) = Field(
        ...,
        description=("List of menu entries to create across main desktop systems."),
    )


def dump_schema_to_json(write=True):
    if write:
        here = Path(__file__).parent
        schema = MenuInstSchema.schema_json(indent=2)
        print(schema)
        with open(here / "data" / "menuinst.schema.json", "w") as f:
            f.write(schema)
            f.write("\n")
    return MenuInstSchema.schema()


def dump_default_to_json(write=True):
    here = Path(__file__).parent
    default_item = MenuItem(
        name="REQUIRED", description="REQUIRED", command=["REQUIRED"], platforms={}
    ).dict()
    default_item["platforms"] = {
        "win": Windows().dict(),
        "osx": MacOS().dict(),
        "linux": Linux().dict(),
    }
    default = MenuInstSchema(
        menu_name="REQUIRED",
        menu_items=[default_item],
        **{
            "$id": "https://schemas.conda.io/menuinst-1.schema.json",
            "$schema": "https://json-schema.org/draft-07/schema",
        },
    ).dict()
    for platform_value in default["menu_items"][0]["platforms"].values():
        for key in list(platform_value.keys()):
            if key in MenuItem.__fields__:
                platform_value.pop(key)
    if write:
        pprint(default)
        with open(here / "data" / "menuinst.default.json", "w") as f:
            json.dump(default, f, indent=2)
            f.write("\n")
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
