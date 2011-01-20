from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^/?$',
        redirect_to, {'url': 'http://hackdns.eu/'}),
    url(r'^root/',
        include('hackdns.root.urls')),
    
    url(r'^_admin/', include(admin.site.urls)),
)
