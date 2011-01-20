from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.http import QueryDict
from functools import wraps
from hackdns.root.models import Server
from M2Crypto.RSA import RSAError

def secure_required(func):
    '''
    Decorator that enforces a secure connection.

        >>> from django.http import HttpResponse
        >>> @secure_required
        >>> def test(request):
        ...     return HttpResponse('Hello world!')

    '''
    @wraps(func)
    def _decorated(request, *args, **kwargs):
        if not request.is_secured:
            return HttpResponseForbidden('Secured connection required. %r' % dict(request.META))
        else:
            return func(request, *args, **kwargs)
    return _decorated

class ServerSecurityMiddleware(object):
    '''
    Adds three properties to the ``request`` object:

        client:: the requesting server
        server:: this server
        is_secured:: boolean

    Don't confuse ``is_secured`` with ``is_secure`` from the CSRF middleware!
    ''' 

    def process_request(self, request):
        request.server = Server.self()
        request.is_secured = False

        # Read potential headers
        content_encryption = request.META.get('HTTP_CONTENT_ENCRYPTION', None)
        server_fqdn  = request.META.get('HTTP_SERVER_FQDN', None)

        # Got them
        if content_encryption and server_fqdn:

            print 'content_encryption', content_encryption
            print 'server_fqdn', server_fqdn

            # Only RSA supported :-)
            if content_encryption.lower() != 'rsa':
                return HttpResponseBadRequest('Content-Encryption not supported.')

            # Lookup server
            try:
                request.client = Server.objects.get(fqdn=server_fqdn, is_active=True)
            except Server.DoesNotExist:
                return HttpResponseForbidden('Server not found.')

            if request.method == 'POST':
                # Decrypt POST-data and stuff it in request.POST
                try:
                    post_encrypted = request.raw_post_data.decode('base64')
                except:
                    return HttpResponseBadRequest('Content decoding failed.')
                try:
                    post_decrypted = request.server.decrypt(request.client,
                        post_encrypted)
                    request.POST = QueryDict(post_decrypted,
                        request._encoding)
                    request.is_secured = True
                except RSAError:
                    return HttpResponseBadRequest('Content decryption failed.')

