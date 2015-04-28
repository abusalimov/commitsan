from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import os
from hookserver import HookServer


github_webhook_secret = os.environ.get('GITHUB_WEBHOOK_SECRET')
if not github_webhook_secret:
    raise RuntimeError('Missing GITHUB_WEBHOOK_SECRET environment variable')

app = HookServer(__name__, bytes(github_webhook_secret, 'utf-8'))
app.config['DEBUG'] = True


@app.hook('ping')
def ping(data, guid):
    return 'pong: {}'.format(data['zen'])
