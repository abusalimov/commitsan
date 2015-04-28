from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import errno
import os
import sys
import subprocess
from subprocess import CalledProcessError

REPOS_PATH = os.path.abspath('repos')


# http://stackoverflow.com/a/600612/545027
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as e:  # Python >2.5
        if e.errno != errno.EEXIST or not os.path.isdir(path):
            raise

def run_cmd(args, bypass_exit_code=False, **kwargs):
    try:
        return subprocess.check_output(args, **kwargs)
    except CalledProcessError:
        if not bypass_exit_code:
            raise

def git_cmd(repo, args, no_git_dir=False):
    repo_path = os.path.join(REPOS_PATH, repo)
    env = {}
    if not no_git_dir:
        env['GIT_DIR'] = repo_path
    return run_cmd(['git'] + args, env=env, cwd=repo_path)

def git_revlist(repo, *commits):
    try:
        out = git_cmd(repo, ['rev-list'] + list(commits) + ['--'])
    except CalledProcessError:
        return []
    else:
        return out.splitlines()

def git_show(repo, commit, format='%B'):
    format_arg = '--format={}'.format(format)  # deal with it
    out = git_cmd(repo, ['show', '--no-patch', format_arg, commit])
    return out

