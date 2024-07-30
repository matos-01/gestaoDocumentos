from os import environ
from sys import path
from os.path import abspath, dirname, join

local = dirname(abspath(__file__))
if local not in path:
    path.append(local)
    path.append(join(local, 'static'))

    environ["DJANGO_SETTINGS_MODULE"] = "panflight.settings"

    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
