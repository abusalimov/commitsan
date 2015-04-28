from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

from git import git_show
from report import report_issue


def msg_non_empty(repo, commit, lines):
    if not any(lines):
        report_issue(repo, commit, 'msg',
                     'Must provide log message')

def msg_subj(repo, commit, lines):
    if not lines:
        return

    empty_line_idx = lines.index('') if '' in lines else len(lines)
    subj_lines = lines[:empty_line_idx]
    body_lines = lines[empty_line_idx+1:]

    if not subj_lines:
        report_issue(repo, commit, 'msg/subj',
                     'Put subject on the first line')
    else:
        if len(subj_lines) > 1:
            report_issue(repo, commit, 'msg/subj-line',
                         'Separate subject from body with a blank line')
        if any(subj_lines[i][-1] == '.' and not subj_lines[i].endswith('..')
               for i in (0, -1)):
            report_issue(repo, commit, 'msg/subj-period',
                         'Do not end the subject line with a period')

def msg_wrap(repo, commit, lines):
    if any(len(line) > 72 and not line.startswith(' '*4) for line in lines):
        report_issue(repo, commit, 'msg/wrap',
                     'Wrap the body at 72 characters')


def check_msg(repo, commit):
    lines = [line.expandtabs().rstrip()
             for line in git_show(repo, commit).splitlines()]

    msg_non_empty(repo, commit, lines)
    msg_subj(repo, commit, lines)
    msg_wrap(repo, commit, lines)

def check_all(repo, commit):
    check_msg(repo, commit)
