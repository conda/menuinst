"""
"""

from .base import Menu, MenuItem


class WindowsMenu(Menu):
    def create(self):
        ...

    def remove(self):
        ...


class WindowsMenuItem(MenuItem):
    def create(self):
        ...

    def remove(self):
        ...
