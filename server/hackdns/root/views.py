from hackdns.root.models import Server
from django.http import HttpResponse

def pubkey(request):
    return HttpResponse(Server.self().key_public,
        content_type='text/plain')

