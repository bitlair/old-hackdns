import uuid
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from hackdns.root.models import Server, Queue


class Vote(models.Model):
    server          = models.ForeignKey(Server)
    content_type    = models.ForeignKey(ContentType)
    object_id       = models.PositiveIntegerField()
    entity          = generic.GenericForeignKey()
    date_created    = models.DateTimeField(auto_now_add=True)
    date_updated    = models.DateTimeField(auto_now=True)
    date_expired    = models.DateTimeField(null=True, blank=True)
    is_positive     = models.BooleanField(blank=True)

    def __unicode__(self):
        return u'<Vote entity=%r>' % (self.entity,)


class Entity(models.Model):
    date_created    = models.DateTimeField(auto_now_add=True)
    date_updated    = models.DateTimeField(auto_now=True)
    date_expired    = models.DateTimeField(null=True, blank=True)
    is_active       = models.BooleanField(default=False, blank=True)
    is_temporary    = models.BooleanField(default=False, blank=True)
    is_placeholder  = models.BooleanField(default=False, blank=True)
    votes           = generic.GenericRelation('Vote')
    ticket          = models.CharField(max_length=32)

    class Meta:
        abstract = True

    def check_votes(self, min_ratio=0.6):
        '''
        Check if this entity received sufficient positive votes.
        '''
        root_servers = Server.all()
        ratio = votes.filter(is_positive=True).count() / float(root_servers.count())
        if ratio >= min_ratio:
            self.is_active = True
            self.save()
            Queue.broadcast('request_entity', entity=self)

    def generate_ticket(self):
        return uuid.uuid4().hex

    def save(self, *args, **kwargs):
        if not self.ticket:
            self.ticket = self.generate_ticket()
        return super(Entity, self).save(*args, **kwargs)


class Group(models.Model):
    name    = models.CharField(max_length=32, unique=True)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        return super(Group, self).save(*args, **kwargs)


class Handle(Entity):
    name            = models.CharField(max_length=32)
    group           = models.ForeignKey('Group', related_name='group')
    email           = models.EmailField()
    email_alt       = models.EmailField(null=True, blank=True)
    key_id          = models.CharField(max_length=255)
    key_data        = models.TextField()
    remark          = models.TextField(default='', blank=True)
    source          = models.ForeignKey('Group', related_name='source')

    class Meta:
        unique_together = (
            ('name', 'group'),
        )

    def __unicode__(self):
        return u'-'.join([self.name, unicode(self.group)])

    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        self.source = Group.objects.get(name='HACK')
        return super(Handle, self).save(*args, **kwargs)


class Zone(models.Model):
    name    = models.CharField(max_length=16, unique=True)
    parent  = models.ForeignKey('self', null=True, blank=True)

    def __unicode__(self):
        if self.parent:
            return u'.'.join([self.name, unicode(self.parent)])
        else:
            return self.name


class Delegation(Entity):
    handle          = models.ForeignKey('Handle')
    domain          = models.CharField(max_length=128)
    zone            = models.ForeignKey('Zone')

    def __unicode__(self):
        return u'.'.join([self.domain, unicode(self.zone)])


class DelegationNameServer(models.Model):
    delegation      = models.ForeignKey('Delegation')
    fqdn            = models.CharField(max_length=128)
    
    def __unicode__(self):
        return self.fqdn

