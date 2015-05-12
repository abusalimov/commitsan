from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import os
from github import GitHub


github_access_token = os.environ.get('GITHUB_ACCESS_TOKEN')
if not github_access_token:
    raise RuntimeError('Missing GITHUB_ACCESS_TOKEN environment variable')
github = GitHub(access_token=github_access_token)

GITHUB_BLOB_URL_TMPL = 'https://github.com/{repo}/blob/master/{filename}'

