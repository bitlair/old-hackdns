from hackdns.root.models import Server
from hackdns.http import JsonResponse
from django.http import HttpResponse
from hackdns.security import secure_required

def pubkey(request):
    return HttpResponse(Server.self().key_public,
        content_type='text/plain')

def list_roots(request):
    return JsonResponse(roots=Server.get_roots())

def list_servers(request):
    servers = {}
    for server in Server.objects.filter(is_active=True):
        servers[server.fqdn] = {
            'fqdn': server.fqdn,
            'ipv4': server.ipv4,
            'ipv6': server.ipv6,
            'key_public': server.key_public,
        }
    return JsonResponse(servers=servers)

@secure_required
def test_secure(request):
    return JsonResponse(status='ok', request=dict(request.POST))

