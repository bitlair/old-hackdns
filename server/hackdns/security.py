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
        server_fqdn = request.META.get('HTTP_SERVER_FQDN', None)

        # Got them
        if content_encryption and server_fqdn:

            print 'content_encryption', content_encryption
            print 'server_fqdn', server_fqdn

            # Lookup server
            try:
                request.client = Server.objects.get(fqdn=server_fqdn, is_active=True)
            except Server.DoesNotExist:
                return HttpResponseForbidden('Server not found.')

            # Chunked RSA-encrypted POST request
            if content_encryption.lower() == 'rsa-chunked':
                if request.method == 'POST':
                    chunks = request.POST.get('chunks', '')
                    # Decrypt POST-data
                    if chunks and chunks.isdigit():
                        chunks = int(chunks)
                        own_key = request.server._private_key
                        his_key = request.client._public_key

                        try:
                            post_decrypted = []
                            for chunk in xrange(0, chunks):
                                own = request.POST.get('his%d' % (chunk,)).decode('base64')
                                his = request.POST.get('own%d' % (chunk,)).decode('base64')
                                post_decrypted.append(request.server.decrypt(request.client, 
                                    his, own, his_key, own_key))
                        except RSAError, e:
                            return HttpResponseBadRequest('Content decryption failed: %r.' % (e, ))
                        except Exception: # for base64 decode
                            return HttpResponseBadRequest('Content decoding failed.')
                        
                        request.POST = QueryDict(''.join(post_decrypted),
                            request._encoding)
                        request.is_secured = True
                        del post_decrypted            

                    else:
                        return HttpResponseBadRequest('Content decoding failed.')

            # Single RSA-encrypted POST request
            elif content_encryption.lower() == 'rsa':
                if request.method == 'POST':
                    try:
                        post_decrypted = request.server.decrypt(request.client,
                            request.POST.get('his').decode('base64'),
                            request.POST.get('own').decode('base64'))
                    except RSAError, e:
                        return HttpResponseBadRequest('Content decryption failed: %r.' % (e, ))
                    except Exception: # for base64 decode
                        return HttpResponseBadRequest('Content decoding failed.')
                    
                    request.POST = QueryDict(post_decrypted,
                        request._encoding)
                    request.is_secured = True
                    del post_decrypted            
                    

            else:
                return HttpResponseBadRequest('Content-Encryption not supported.')
