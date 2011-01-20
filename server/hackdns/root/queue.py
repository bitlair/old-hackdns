from hackdns.root.models import Queue
try:
    import dns
except ImportError:
    print 'python-dnspython is required'
    raise

