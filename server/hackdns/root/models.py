import datetime
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
try:
    import json
except ImportError:
    from django.utils import simplejson as json


class Server(models.Model):
    fqdn            = models.CharField(max_length=255, unique=True)
    ipv4            = models.CharField(max_length=15, null=True, blank=True)
    ipv6            = models.CharField(max_length=40, null=True, blank=True)

    date_created    = models.DateTimeField(auto_now_add=True)
    date_updated    = models.DateTimeField(auto_now=True)

    is_active       = models.BooleanField(blank=True)

    def __unicode__(self):
        return self.fqdn

    @staticmethod
    def all():
        return Server.objects.filter(is_active=True)

    @staticmethod
    def self():
        return Server.objects.get(fqdn=settings.HACKDNS_SERVER_FQDN)


class Queue(models.Model):
    src_server      = models.ForeignKey('Server')
    dst_server      = models.ForeignKey('Server')
    date_created    = models.DateTimeField(auto_now_add=True)
    date_updated    = models.DateTimeField(auto_now=True)
    date_expired    = models.DateTimeField(blank=True, null=True)
    date_delivered  = models.DateTimeField(blank=True, null=True)
    call            = models.CharField(max_length=32)
    args            = models.TextField()

    @staticmethod
    def broadcast(call, entity=None, **args):
        if entity:
            args[u'content_type'] = ContentType.objects.get_for_model(entity)
            args[u'content_name'] = unicode(entity)

        for server in Server.all():
            Queue(src_server=Server.self,
                dst_server=server,
                call=call,
                args=args).save()

    def save(self, *args, **kwargs):
        if not isinstance(self.args, basestring):
            self.args = json.dumps(self.args)
        if not self.date_expired:
            self.date_expired = datetime.datetime.now() + \
                datetime.timedelta(secs=settings.HACKDNS_QUEUE_TTL)
        return super(Queue, self).save(*args, **kwargs)

