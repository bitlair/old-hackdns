import datetime
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from M2Crypto import BIO, RSA
from dns import rdatatype
from dns.exception import DNSException
from dns.resolver import Resolver
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
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
    key_public      = models.CharField(max_length=255)
    key_private     = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.fqdn

    @property
    def address(self):
        addresses = {}
        if self.ipv4:
            addresses[self.ipv4] = True
        if self.ipv6:
            addresses[self.ipv6] = True
        return addresses.keys()[0]

    @staticmethod
    def all():
        return Server.objects.filter(is_active=True)

    @staticmethod
    def self():
        return Server.objects.get(fqdn=settings.HACKDNS_SERVER_FQDN)

    @staticmethod
    def get_resolver(server=None):
        if server is None:
            server = Server.self()

        resolver = Resolver()
        resolver.reset()
        resolvconf = StringIO()
        if server.ipv4:
            resolvconf.write('nameserver %s\n' % (server.ipv4,))
        if server.ipv6:
            resolvconf.write('nameserver %s\n' % (server.ipv6,))
        resolver.read_resolv_conf(resolvconf)
        return resolver

    @staticmethod
    def get_roots():
        resolver = Server.get_resolver()
        servers = []
        for answer in resolver.query('hack.', rdatatype.NS):
            if answer.__class__.__name__ == 'NS':
                fqdn = str(answer).rstrip('.')
                servers.append(fqdn)
        return servers

    def encrypt(self, other, message):
        '''
        Encrypt message to other server. The message must be a byte string.
        '''
        own_bio = BIO.MemoryBuffer(str(self.key_private))
        own_rsa = RSA.load_key_bio(own_bio)
        his_bio = BIO.MemoryBuffer(str(other.key_public))
        his_rsa = RSA.load_pub_key_bio(his_bio)
        return his_rsa.public_encrypt(message, RSA.pkcs1_padding)

    def decrypt(self, other, message):
        own_bio = BIO.MemoryBuffer(str(self.key_private))
        own_rsa = RSA.load_key_bio(own_bio)
        his_bio = BIO.MemoryBuffer(str(other.key_public))
        his_rsa = RSA.load_pub_key_bio(his_bio)
        return own_rsa.private_decrypt(message, RSA.pkcs1_padding)


class Queue(models.Model):
    src_server      = models.ForeignKey('Server', related_name='src')
    dst_server      = models.ForeignKey('Server', related_name='dst')
    date_created    = models.DateTimeField(auto_now_add=True)
    date_updated    = models.DateTimeField(auto_now=True)
    date_expired    = models.DateTimeField(blank=True, null=True)
    date_delivered  = models.DateTimeField(blank=True, null=True)
    call            = models.CharField(max_length=32)
    args            = models.TextField()
    parent          = models.ForeignKey('self', null=True, blank=True)

    @staticmethod
    def broadcast(call, entity=None, **args):
        '''
        Queue a broadcast message (for all root servers).
        '''
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

