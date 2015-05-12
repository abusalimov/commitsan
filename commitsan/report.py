from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

from github import ApiError

from commitsan.github import github, GITHUB_BLOB_URL_TMPL
from commitsan.worker import job

CONTRIBUTING_FILENAME = 'CONTRIBUTING.md'


def output(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    print(*args, **kwargs)

@job()
def post_status(repo, commit, context, description, state='pending', **kwargs):
    endpoint = github.repos(repo).statuses(commit)
    if 'target_url' not in kwargs:
        kwargs['target_url'] = (GITHUB_BLOB_URL_TMPL
                                .format(filename=CONTRIBUTING_FILENAME,
                                        **locals()))
    output('Posting to {repo}: state of {commit} set to {state}: '
           '{context} ({description})'
           .format(**dict(kwargs, **locals())))
    endpoint.post(context='commitsan/{}'.format(context),
                  description=description, state=state, **kwargs)

def report_issue(repo, commit, context, description, fatal=False):
    post_status.delay(repo, commit, context, description,
                      state='failure' if fatal else 'pending')
