import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'hackdns.settings'
os.umask(0002)

DOCUMENT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(DOCUMENT_ROOT)
sys.path.append(os.path.dirname(DOCUMENT_ROOT))

# mod_wsgi will break if you print to stdout
sys.stdout = sys.stderr

def application(environ, start_response):
    import django.core.handlers.wsgi
    _application = django.core.handlers.wsgi.WSGIHandler()
    return _application(environ, start_response)

