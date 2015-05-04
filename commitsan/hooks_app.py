from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import os
from hookserver import HookServer

from commitsan import repos


github_webhook_secret = os.environ.get('GITHUB_WEBHOOK_SECRET')
if not github_webhook_secret:
    raise RuntimeError('Missing GITHUB_WEBHOOK_SECRET environment variable')

app = HookServer(__name__, bytes(github_webhook_secret, 'utf-8'))
app.config['DEBUG'] = True


NULL_SHA = '0'*40

@app.hook('ping')
def ping(data, guid):
    repo = data['repository']
    repos.update_repo.delay(repo['full_name'], repo['clone_url'])

    return 'pong: {}'.format(data['zen'])

@app.hook('push')
def push(data, guid):
    repo = data['repository']
    update_job = repos.update_repo.delay(repo['full_name'], repo['clone_url'])

    from_commit = data['before']
    to_commit = data['after']

    if to_commit != NULL_SHA:  # skip branch deletions
        if from_commit == NULL_SHA:
            from_commit = 'master'
        commit_range = '{}..{}'.format(from_commit, to_commit)

        repos.process_commit_range.delay(repo['full_name'], commit_range,
                                         depends_on=update_job)

    return 'OK'
