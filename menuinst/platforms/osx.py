"""
"""

from .base import Menu, MenuItem


class MacOSMenu(Menu):
    def create(self):
        ...

    def remove(self):
        ...


class MacOSMenuItem(MenuItem):
    def create(self):
        ...

    def remove(self):
        ...
