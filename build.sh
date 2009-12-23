#!/bin/sh

rm -rf build dist
python setup.py bdist_egg
index-tool repack -v dist/AppInst-*.egg
# remove setuptools egg
rm dist/AppInst-*py2*.egg
