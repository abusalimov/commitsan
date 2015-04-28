from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import os
import shutil
import sys
from rq import Queue
from rq.decorators import job

from git import REPOS_PATH, CalledProcessError, git_cmd, git_revlist, mkdir_p
from worker import REDIS_CONN

q = Queue(connection=REDIS_CONN)


def output(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    print(*args, **kwargs)


@job(q)
def update_repo(repo, clone_url):
    try:
        out = git_cmd(repo, ['remote', 'update'])
    except (OSError, CalledProcessError):
        repo_path = os.path.join(REPOS_PATH, repo)
        shutil.rmtree(repo_path, ignore_errors=True)
        mkdir_p(repo_path)
        out = git_cmd(repo, ['clone', '--mirror', clone_url, '.'],
                      no_git_dir=True)

    output(out)


@job(q)
def process_commit_range(repo, *commits):
    for commit in git_revlist(repo, *commits):
        process_commit(repo, commit)


def process_commit(repo, commit):
    reports = []
    add_report = reports.append

    lines = [line.expandtabs() for line in git_show(repo, commit).splitlines()]

    if not lines:
        add_report(report.empty_message)
    else:
        if len(lines) > 1 and lines[1]:
            add_report(report.non_empty_message_line_after_subject)
        for line in lines:
            if len(line) > 72 and not line.startswith(' '*4):
                add_report(report.too_long_message_line)

    for job_func in sorted(reports):
        job_func.delay(repo, commit)

