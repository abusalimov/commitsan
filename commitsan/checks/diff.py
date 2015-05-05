from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

from commitsan.checks import checker
from commitsan.git import git_diff_check


@checker
def check_diff(repo, commit):
    bad_lines = git_diff_check(repo, commit)
    if bad_lines:
        single = (bad_lines == 1)
        yield ('error', 'diff',
               ('{} line{plural} introduce{singular} whitespace errors'
                .format(bad_lines,
                        plural='s'*(not single), singular='s'*single)))

