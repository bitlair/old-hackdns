from django.contrib import admin
from hackdns.root.models import Server, Queue

admin.site.register(Server)
admin.site.register(Queue)

