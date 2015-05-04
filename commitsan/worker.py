from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import os
import redis
from rq import Worker, Queue, Connection


listen = ['high', 'default', 'low']

REDIS_URL = os.environ.get('REDISTOGO_URL', 'redis://localhost:6379')
REDIS_CONN = redis.from_url(REDIS_URL)


if __name__ == '__main__':
    with Connection(REDIS_CONN):
        worker = Worker([Queue(prio) for prio in listen])
        worker.work()
