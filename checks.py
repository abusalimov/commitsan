from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

from git import git_show
from report import report_issue


def msg_non_empty(repo, commit, lines):
    if not lines:
        report_issue(repo, commit, 'msg',
                     'Must provide log message')

def msg_subj_line(repo, commit, lines):
    if len(lines) > 1 and lines[1]:
        report_issue(repo, commit, 'msg/subj-line',
                     'Separate subject from body with a blank line')

def msg_wrap(repo, commit, lines):
    for line in lines:
        if len(line) > 72 and not line.startswith(' '*4):
            report_issue(repo, commit, 'msg/wrap',
                         'Wrap the body at 72 characters')
            break


def check_msg(repo, commit):
    lines = [line.expandtabs().rstrip()
             for line in git_show(repo, commit).splitlines()]

    msg_non_empty(repo, commit, lines)
    msg_subj_line(repo, commit, lines)
    msg_wrap(repo, commit, lines)

def check_all(repo, commit):
    check_msg(repo, commit)
