from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

from commitsan.report import report_issue
from commitsan.util import unique


checker_registry = []

def checker(func):
    checker_registry.append(func)
    return func

def check_all(repo, commit):
    def gen_issues():
        for checker_func in checker_registry:
            for issue in checker_func(repo, commit):
                yield issue

    for level, context, description in unique(gen_issues(), key=lambda i:i[1]):
        report_issue(repo, commit, context, description,
                     fatal=(level in ['fatal', 'failure', 'error']))

from . import msg
from . import diff
