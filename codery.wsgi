import os, sys
from os.path import expanduser, join

sys.path.append(os.path.dirname(__file__))
os.environ['DJANGO_SETTINGS_MODULE'] = 'codery.settings'

import codery.settings
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

