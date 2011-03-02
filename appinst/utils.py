# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.

from xml.etree import ElementTree


class ShortcutCreationError(Exception):
    pass


XMLindentation = "    "

def indent(elem, level=0):
    "Adds whitespace to the tree, so that it results in a pretty printed tree."
    i = "\n" + level * XMLindentation
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + XMLindentation
        for e in elem:
            indent(e, level+1)
            if not e.tail or not e.tail.strip():
                e.tail = i + XMLindentation
        if not e.tail or not e.tail.strip():
            e.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def add_dtd_and_format(path):
    tree = ElementTree.ElementTree(None, path)
    indent(tree.getroot())
    fo = open(path, 'w')
    fo.write("""\
<!DOCTYPE Menu
  PUBLIC '-//freedesktop//DTD Menu 1.0//EN'
  'http://standards.freedesktop.org/menu-spec/menu-1.0.dtd'>
""")
    tree.write(fo)
    fo.write('\n')
    fo.close()


if __name__ == '__main__':
    add_dtd_and_format('z.xml')
