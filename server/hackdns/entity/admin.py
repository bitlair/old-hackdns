from django.contrib import admin
from hackdns.entity.models import *

class DelegationNameServerAdmin(admin.ModelAdmin):
    list_display = ('delegation', 'fqdn')

admin.site.register(Vote)
admin.site.register(Entity)
admin.site.register(Group)
admin.site.register(Handle)
admin.site.register(Zone)
admin.site.register(Delegation)
admin.site.register(DelegationNameServer, DelegationNameServerAdmin)
