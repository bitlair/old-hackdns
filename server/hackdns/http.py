from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
try:
    import json
except ImportError:
    from django.utils import simplejson as json

def Response(request, template, **data):
    return render_to_response(template, data,
        context_instance=RequestContext(request))

def JsonResponse(**data):
    serialized = json.dumps(data, indent=2)
    return HttpResponse(serialized,
        content_type='text/plain') # FIXME: application/json

