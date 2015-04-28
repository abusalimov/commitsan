from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

from flask import Flask

from hooks_app import app as hooks


frontend = Flask(__name__)
frontend.config['DEBUG'] = True


class CombiningMiddleware(object):
    """Allows one to mount middlewares or applications in a WSGI application.

    Unlike DispatcherMiddleware, this one doesn't alter the environment of the
    called application. That is, applications still receive the absolute path.
    """

    def __init__(self, app, mounts=None):
        self.app = app
        self.mounts = mounts or {}

    def __call__(self, environ, start_response):
        script = environ.get('PATH_INFO', '')
        while '/' in script:
            if script in self.mounts:
                app = self.mounts[script]
                break
            script = script.rsplit('/', 1)[0]
        else:
            app = self.mounts.get(script, self.app)
        return app(environ, start_response)


app = CombiningMiddleware(frontend, {
    '/hooks':     hooks,
})


@frontend.route('/')
def hello():
    return 'Hello World!'
