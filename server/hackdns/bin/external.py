import os
import sys

HACKDNS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if not 'DJANGO_SETTINGS_MODULE' in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'hackdns.settings_production'
if not HACKDNS_ROOT in sys.path:
    sys.path.append(HACKDNS_ROOT)
if not os.path.dirname(HACKDNS_ROOT) in sys.path:
    sys.path.append(os.path.dirname(HACKDNS_ROOT))

del os
del sys
