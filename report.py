from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import os
from github import GitHub, ApiError
from rq import Queue
from rq.decorators import job

from worker import REDIS_CONN

q = Queue(connection=REDIS_CONN)


github_access_token = os.environ.get('GITHUB_ACCESS_TOKEN')
if not github_access_token:
    raise RuntimeError('Missing GITHUB_ACCESS_TOKEN environment variable')
github = GitHub(access_token=github_access_token)

GITHUB_BLOB_URL_TMPL = 'https://github.com/{repo}/blob/master/{filename}'
CONTRIBUTING_FILENAME = 'CONTRIBUTING.md'


def output(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    print(*args, **kwargs)

def post_status(repo, commit, context, state='failure', **kwargs):
    endpoint = github.repos(repo).statuses(commit)
    if 'target_url' not in kwargs:
        kwargs['target_url'] = (GITHUB_BLOB_URL_TMPL
                                .format(filename=CONTRIBUTING_FILENAME,
                                        **locals()))
    output('Posting to {repo}: state of {commit} set to {state}: '
           '{context} ({description})'
           .format(**dict(kwargs, **locals())))
    endpoint.post(context='commitsan/{}'.format(context),
                  state=state, **kwargs)


@job(q)
def empty_message(repo, commit):
    post_status(repo, commit, 'msg/empty',
                description='Must provide log message')

@job(q)
def non_empty_message_line_after_subject(repo, commit):
    post_status(repo, commit, 'msg/subj',
                description='Separate subject from body with a blank line')

@job(q)
def too_long_message_line(repo, commit):
    post_status(repo, commit, 'msg/wrap',
                description='Wrap the body at 72 characters')
