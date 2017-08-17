# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2013-2017 Continuum Analytics, Inc.
# Copyright (c) 2008-2011 by Enthought, Inc.
# All rights reserved.
#
# Licensed under the terms of the BSD 3-clause License (See LICENSE.txt)
# -----------------------------------------------------------------------------
"""Menuinst: Cross platform menu item installation."""

from __future__ import absolute_import

# Local imports
from ._version import get_versions
from .api import install

install= install

__version__ = get_versions()['version']
del get_versions
