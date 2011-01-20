import os
import sys

HACKDNS_ROOT = os.path.dirname(os.path.abspath(__file__))

if not 'DJANGO_SETTINGS_MODULE' in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_test'
if not HACKDNS_ROOT in sys.path:
    sys.path.append(HACKDNS_ROOT)

from hackdns.root.queue import run_queue

