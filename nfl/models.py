
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
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

class Week(TimestampMixin):
    primary_key = models.CharField(primary_key=True, max_length=7,
        editable=False, blank=True, unique=True, auto_created=True)
    season = models.ForeignKey(Season, related_name="weeks")
    number = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(21)])
    first_game = models.DateTimeField()
    last_game = models.DateTimeField()

    class Meta(object):
        ordering = ['number']

    def save(self, **kwargs):
        self.primary_key = "%s-%s" % (self.season.pk, self.number)
        super(Week, self).save(**kwargs)

    @classmethod
    def get_by_season(cls, season):
        return cls.objects.filter(season=season)

class Game(TimestampMixin):
    """
    Game Matchup
    """
    primary_key = models.CharField(primary_key=True, max_length=10,
        editable=False, blank=True, unique=True, auto_created=True)
    week = models.ForeignKey(Week, related_name="games")
    number = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(16)])
    home = models.ForeignKey(Team, verbose_name="Home Team", related_name="home_games")
    away = models.ForeignKey(Team, verbose_name="Away Team", related_name="away_games")
    game_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta(object):
        ordering = ['week__number', '-game_time']

    def __unicode__(self):
        return "%s vs. %s" % (self.home_id, self.away_id)
    
    def save(self, **kwargs):
        self.primary_key = "%s-%s" % (self.week.pk, self.number)
        super(Game, self).save(**kwargs)