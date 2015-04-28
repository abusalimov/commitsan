from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import errno
import os
import shutil
import sys
import subprocess
from subprocess import STDOUT, CalledProcessError
from rq import Queue
from rq.decorators import job

from worker import REDIS_CONN
import report

q = Queue(connection=REDIS_CONN)


REPOS_PATH = os.path.abspath('repos')


def output(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    print(*args, **kwargs)

# http://stackoverflow.com/a/600612/545027
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as e:  # Python >2.5
        if e.errno != errno.EEXIST or not os.path.isdir(path):
            raise

def run_cmd(args, bypass_exit_code=False, **kwargs):
    try:
        return subprocess.check_output(args, stderr=STDOUT, **kwargs)
    except CalledProcessError as e:
        output(str(e))
        if not bypass_exit_code:
            raise
    except OSError as e:
        output(str(e))
        raise

def run_git(repo, args, no_git_dir=False):
    repo_path = os.path.join(REPOS_PATH, repo)
    env = {}
    if not no_git_dir:
        env['GIT_DIR'] = repo_path
    return run_cmd(['git'] + args, env=env, cwd=repo_path)

def git_revlist(repo, *commits):
    out = run_git(repo, ['rev-list'] + list(commits) + ['--'])
    return out.splitlines()

def git_show(repo, commit, format='%B'):
    format_arg = '--format={}'.format(format)  # deal with it
    out = run_git(repo, ['show', '--no-patch', format_arg, commit])
    return out


@job(q)
def update_repo(repo, clone_url):
    try:
        out = run_git(repo, ['remote', 'update'])
    except (OSError, CalledProcessError):
        repo_path = os.path.join(REPOS_PATH, repo)
        shutil.rmtree(repo_path, ignore_errors=True)
        mkdir_p(repo_path)
        out = run_git(repo, ['clone', '--mirror', clone_url, '.'],
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

