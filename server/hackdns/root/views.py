from hackdns.root.models import Server
from hackdns.http import JsonResponse
from django.http import HttpResponse

def pubkey(request):
    return HttpResponse(Server.self().key_public,
        content_type='text/plain')

def list_roots(request):
    return JsonResponse(roots=Server.get_roots())

def list_servers(request):
    servers = Server.objects.all(is_active=True)
    return JsonResponse(servers=({
            'fqdn': server.fqdn,
            'ipv4': server.ipv4,
            'ipv6': server.ipv6,
        } for server in servers))
