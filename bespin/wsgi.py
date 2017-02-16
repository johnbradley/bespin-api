"""
WSGI config for bespin project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bespin.settings_prod")

env_variables_to_pass = [
  'BESPIN_SECRET_KEY',
  'BESPIN_ALLOWED_HOST',
  'BESPIN_DB_NAME',
  'BESPIN_DB_USER',
  'BESPIN_DB_PASSWORD',
  'BESPIN_DB_HOST',
  'BESPIN_CORS_HOST',
  'BESPIN_STATIC_ROOT',
]

def application(environ, start_response):
     # pass the WSGI environment variables on through to os.environ
     for var in env_variables_to_pass:
         os.environ[var] = environ.get(var, '')
     _application = get_wsgi_application()
     return _application(environ, start_response)
