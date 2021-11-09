import xml.etree.ElementTree as XMLTree


def slugify(text):
    non_url_safe = (
        '"',
        "#",
        "$",
        "%",
        "&",
        "+",
        ",",
        "/",
        ":",
        ";",
        "=",
        "?",
        "@",
        "[",
        "\\",
        "]",
        "^",
        "`",
        "{",
        "|",
        "}",
        "~",
        "'",
    )
    translate_table = {ord(char): "" for char in non_url_safe}
    return "_".join(text.translate(translate_table).split())


def indent_xml_tree(elem, level=0):
    """
    adds whitespace to the tree, so that it results in a pretty printed tree
    """
    indentation = "    "  # 4 spaces, just like in Python!
    base_indentation = "\n" + level * indentation
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = base_indentation + indentation
        for e in elem:
            indent_xml_tree(e, level + 1)
            if not e.tail or not e.tail.strip():
                e.tail = base_indentation + indentation
        if not e.tail or not e.tail.strip():
            e.tail = base_indentation
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = base_indentation


def add_xml_child(parent, tag, text=None):
    """
    Add a child element of specified tag type to parent.
    The new child element is returned.
    """
    elem = XMLTree.SubElement(parent, tag)
    if text is not None:
        elem.text = text
    return elem


class WinLex:
    @classmethod
    def quote_args(cls, args):
        # cmd.exe /K or /C expects a single string argument and requires
        # doubled-up quotes when any sub-arguments have spaces:
        # https://stackoverflow.com/a/6378038/3257826
        if (
            len(args) > 2
            and ("CMD.EXE" in args[0].upper() or "%COMSPEC%" in args[0].upper())
            and (args[1].upper() == "/K" or args[1].upper() == "/C")
            and any(" " in arg for arg in args[2:])
        ):
            args = [
                cls.ensure_pad(args[0], '"'),  # cmd.exe
                args[1],  # /K or /C
                '"%s"' % (" ".join(cls.ensure_pad(arg, '"') for arg in args[2:])),  # double-quoted
            ]
        else:
            args = [cls.quote_string(arg) for arg in args]
        return args

    @classmethod
    def quote_string(cls, s):
        """
        quotes a string if necessary.
        """
        # strip any existing quotes
        s = s.strip('"')
        # don't add quotes for minus or leading space
        if s[0] in ("-", " "):
            return s
        if " " in s or "/" in s:
            return '"%s"' % s
        else:
            return s

    @classmethod
    def ensure_pad(cls, name, pad="_"):
        """

        Examples:
            >>> ensure_pad('conda')
            '_conda_'

        """
        if not name or name[0] == name[-1] == pad:
            return name
        else:
            return "%s%s%s" % (pad, name, pad)
