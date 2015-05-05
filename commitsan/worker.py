from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import os
import redis
from rq import Worker, Queue, Connection
import rq.decorators


listen = ['high', 'default', 'low']

REDIS_URL = os.environ.get('REDISTOGO_URL', 'redis://localhost:6379')
REDIS_CONN = redis.from_url(REDIS_URL)


class job(rq.decorators.job):
    """Extends @job deco maker adding reasonable defaults for constructor
    arguments.
    """

    def __init__(self, queue='default', connection=REDIS_CONN, **kwargs):
        super(job, self).__init__(queue, connection=connection, **kwargs)


if __name__ == '__main__':
    with Connection(REDIS_CONN):
        worker = Worker([Queue(prio) for prio in listen])
        worker.work()
