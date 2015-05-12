from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *


def unique(iterable, key=id):
    """
    List unique elements, preserving order. Remember all elements ever seen.
    """
    return unique_values((key(element), element) for element in iterable)

def unique_values(pairs):
    seen = set()
    seen_add = seen.add
    for k, v in pairs:
        if k not in seen:
            seen_add(k)
            yield v

