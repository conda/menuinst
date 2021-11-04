"""
"""

from .base import Menu, MenuItem


class LinuxMenu(Menu):
    def create(self):
        ...

    def remove(self):
        ...


class LinuxMenuItem(MenuItem):
    def create(self):
        ...

    def remove(self):
        ...
