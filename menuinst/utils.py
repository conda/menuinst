# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2013-2017 Continuum Analytics, Inc.
# Copyright (c) 2008-2011 by Enthought, Inc.
# All rights reserved.
#
# Licensed under the terms of the BSD 3-clause License (See LICENSE.txt)
# -----------------------------------------------------------------------------
"""File and directory removal utilities."""

# Standard library imports
import os
import shutil


def rm_empty_dir(path):
    try:
        os.rmdir(path)
    except OSError:  # Directory might not exist or not be empty
        pass


def rm_rf(path):
    if os.path.islink(path) or os.path.isfile(path):
        # Note that we have to check if the destination is a link because
        # exists('/path/to/dead-link') will return False, although
        # islink('/path/to/dead-link') is True.
        os.unlink(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
