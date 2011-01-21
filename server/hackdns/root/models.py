import datetime
import itertools
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
    def _private_key(self):
        bio = BIO.MemoryBuffer(str(self.key_private))
        key = RSA.load_key_bio(bio)
        return key

    @property
    def _public_key(self):
        bio = BIO.MemoryBuffer(str(self.key_public))
        key = RSA.load_pub_key_bio(bio)
        return key

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
        bio = BIO.MemoryBuffer(str(other.key_public))
        rsa = RSA.load_pub_key_bio(his_bio)
        return his_rsa.public_encrypt(message, RSA.pkcs1_padding)

    def decrypt(self, other, his, own, his_key=None, own_key=None):
        if not his_key:
            his_key = other._public_key
        if not own_key:
            own_key = Server.self()._private_key

        # Decrypt
        his_raw = his_key.public_decrypt(his, RSA.pkcs1_padding)
        own_raw = own_key.private_decrypt(own, RSA.pkcs1_padding)
        assert his_raw == own_raw
        return his_raw

    def verify(self, signer, data, signature, algorithm='sha1'):
        '''
        Verify an RSA signature.
        '''
        bio = BIO.MemoryBuffer(str(signer.key_public))
        rsa = RSA.load_pub_key_bio(bio)
        return rsa.verify(data, signature, algo=algorithm)

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

