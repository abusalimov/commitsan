from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import os
from hookserver import HookServer

import git_jobs


github_webhook_secret = os.environ.get('GITHUB_WEBHOOK_SECRET')
if not github_webhook_secret:
    raise RuntimeError('Missing GITHUB_WEBHOOK_SECRET environment variable')

app = HookServer(__name__, bytes(github_webhook_secret, 'utf-8'))
app.config['DEBUG'] = True


@app.hook('ping')
def ping(data, guid):
    repo = data['repository']
    git_jobs.update_repo.delay(repo['full_name'], repo['clone_url'])

    return 'pong: {}'.format(data['zen'])

@app.hook('push')
def push(data, guid):
    repo = data['repository']
    update_job = git_jobs.update_repo.delay(repo['full_name'],
                                            repo['clone_url'])
    git_jobs.process_commits.delay(repo['full_name'],
                               data['before'], data['after'],
                               depends_on=update_job)

    return 'OK'
