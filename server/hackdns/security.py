import hashlib
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.http import QueryDict
from functools import wraps
from hackdns.root.models import Server
from M2Crypto.RSA import RSAError


HASH_ALGO = {
    'md5':    hashlib.md5,
    'sha1':   hashlib.sha1,
    'sha224': hashlib.sha224,
    'sha256': hashlib.sha256,
    'sha384': hashlib.sha384,
    'sha512': hashlib.sha512,
}


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
            return HttpResponseForbidden('Secured connection required.')
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
        content_hash = request.META.get('HTTP_CONTENT_HASH', None)
        content_signature = request.META.get('HTTP_CONTENT_SIGNATURE', None)
        server_fqdn  = request.META.get('HTTP_SERVER_FQDN', None)

        # Got them
        if content_encryption and content_hash and content_signature and server_fqdn:

            print 'content_encryption', content_encryption
            print 'content_hash', content_hash
            print 'content_signature', content_signature
            print 'server_fqdn', server_fqdn

            # Only RSA supported :-)
            if content_encryption.lower() != 'rsa':
                return HttpResponseBadRequest('Content-Encryption not supported.')

            try:
                algorithm, post_hash = map(lambda x: x.strip().lower(),
                    content_hash.split(';'))
            except ValueError:
                return HttpResponseBadRequest('Content-Hash invalid.')
            else:
                if algorithm.lower() not in HASH_ALGO:
                    return HttpResponseBadRequest('Content-Hash unsupported method.')

            try:
                signature = content_signature.decode('base64')
            except:
                return HttpResponseBadRequest('Content-Signature decoding failed.')

            # Lookup server
            try:
                request.client = Server.objects.get(fqdn=server_fqdn, is_active=True)
            except Server.DoesNotExist:
                return HttpResponseForbidden('Server not found.')

            if request.method == 'POST':
                # Decrypt POST-data
                try:
                    post_encrypted = request.raw_post_data.decode('base64')
                except:
                    return HttpResponseBadRequest('Content decoding failed.')
                try:
                    post_decrypted = request.server.decrypt(request.client,
                        post_encrypted)
                except RSAError:
                    return HttpResponseBadRequest('Content decryption failed.')

                # Check POST-data hash signature
                try:
                    request.server.verify(request.server,
                        post_hash, signature, algorithm)
                except Exception, e:
                    raise
                    return HttpResponseBadRequest(str(e))

                # check POST-data hash
                #hash_func = HASH_ALGO[algorithm.lower()]
                #post_decrypted_hash = hash_func(post_decrypted).hexdigest()
                #if post_decrypted_hash != hash:
                #    return HttpResponseBadRequest('Content-Hash invalid.')
                
                request.POST = QueryDict(post_decrypted,
                    request._encoding)
                request.is_secured = True

