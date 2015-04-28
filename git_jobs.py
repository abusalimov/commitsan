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
def process_commit_range(repo, before, after):
    pass

