# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.
#
# FIXME: Currently, this file holds a small amount of code common to all the
# linux platforms. In the future, this should have a great deal more, as there
# is quite a bit of code reuse among each platform-specific script.
#

def build_id(current_id, previous_id):
    """Takes a string and prepends a second string if the second string exists,
    using a period as a delimiter.
    """
    
    if len(previous_id) > 1:
        current_id = '%s.%s' % (previous_id, current_id)

    return current_id

def fix_shortcut_ids(shortcuts, mapped_ids):
    """Takes the id of a shortcut and prepends the id of its menu hierarchy.
    
    Parameters
    ----------
    shortcuts: list of dicts
        Contains the list of shortcuts to be altered.
    mapped_ids: dict
        Contains ids mapped to unique categories. When one of these categories
        is matched with the category in a shortcut, the corresponing id is
        prepended to the id of the shortcut

    Description
    -----------
    Modified in-place shortcut IDs to contain IDs of their containing menus. An
    ID of "itemiID" might become "menuID.submenuID.itemID".
    """

    for shortcut in shortcuts:
        shortcut['id'] = mapped_ids[shortcut['categories'][0]] + '.' + shortcut['id']
