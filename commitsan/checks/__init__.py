from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

from commitsan.report import report_issue


checker_registry = []

def checker(func):
    checker_registry.append(func)
    return func

def check_all(repo, commit):
    for checker_func in checker_registry:
        for level, context, description in checker_func(repo, commit):
            report_issue(repo, commit, context, description,
                         fatal=(level in ['fatal', 'failure', 'error']))


from . import msg
from . import diff
