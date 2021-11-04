"""
"""
from typing import Union, Literal
import sys

from ..schema import MenuItemMetadata


class Menu:
    def __init__(
        self,
        name: str,
        prefix: str = sys.prefix,
        base_prefix: str = sys.prefix,
        mode: Union[Literal["user"], Literal["admin"]] = "user",
    ):
        self.name = name
        self.prefix = prefix
        self.base_prefix = base_prefix
        assert mode in ("user", "admin"), f"`mode` must be either `user` or `admin`"
        self.mode = mode

    def create(self):
        raise NotImplementedError

    def remove(self):
        raise NotImplementedError


class MenuItem:
    def __init__(self, menu: Menu, metadata: MenuItemMetadata):
        self.menu = menu
        self.metadata = metadata

    def create(self):
        raise NotImplementedError

    def remove(self):
        raise NotImplementedError
