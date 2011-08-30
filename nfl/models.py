
from django.core.validators import RegexValidator
from django.core.cache import cache
from django.db import models
from django.utils.encoding import force_unicode


class TimestampMixin(models.Model):
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta(object):
        abstract = True

class Division(TimestampMixin):
    AFC, NFC = "AFC", "NFC"
    CONFERENCES = ((AFC, AFC), (NFC, NFC))
    REGIONS = (
        ('North', 'North'),
        ('South', 'South'),
        ('East', 'East'),
        ('West', 'West'),
    )
    primary_key = models.CharField(primary_key=True, max_length=9,
        editable=False, blank=True, unique=True, auto_created=True)
    conference = models.CharField(max_length=3, choices=CONFERENCES)
    region = models.CharField(max_length=5, choices=REGIONS)

    def __unicode__(self):
        return force_unicode("%s %s" % (self.conference, self.region))

    def save(self, **kwargs):
        self.primary_key = "%s-%s" % (self.conference, self.region)
        super(Division, self).save(**kwargs)

class Season(TimestampMixin):
    year = models.CharField(primary_key=True, max_length=4,
                            validators=[RegexValidator(r'^\d{4}$')])
    is_active = models.BooleanField()

    class Meta(object):
        ordering = ('is_active', '-year')

    def __unicode__(self):
        return force_unicode(self.year)

    def save(self, **kwargs):
        if self.is_active:
            Season.objects.update(is_active=False)
        super(Season, self).save(**kwargs)

    @classmethod
    def active_season(cls):
        return cls.objects.get(is_active=True)

class Team(TimestampMixin):
    abbr = models.CharField(primary_key=True, max_length=3)
    name = models.CharField(max_length=10)
    division = models.ForeignKey(Division, related_name="teams")
    is_active = models.BooleanField(default=True)

    class Meta(object):
        ordering = ('is_active', 'name',)

    def __unicode__(self):
        return force_unicode(self.name)

    @classmethod
    def all_teams(cls):
        cache_key = 'all_teams'
        all_teams = cache.get(cache_key)
        if all_teams is None:
            all_teams = list(cls.objects.filter(is_active=True))
            cache.set(cache_key, all_teams, timeout=2.6*1e6)
        return all_teams

