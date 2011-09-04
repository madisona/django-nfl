
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.encoding import force_unicode

from nfl import tz, utils

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
        qs = cls.objects.filter(is_active=True)
        return utils.get_or_add_qs('all_teams', qs, timeout=2.6*1e6)

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
    def season_weeks(cls, season):
        return cls.objects.filter(season=season)

    @classmethod
    def active_weeks(cls):
        qs = cls.objects.filter(season__is_active=True)
        return utils.get_or_add_qs('active_weeks', qs, timeout=2.6*1e6)

    @classmethod
    def current_week(cls, week_key=None, date_trigger="first_game", delay=False):
        """
        Returns current week based on current time. Currently makes a
        big assumption that the first_game is stored in Eastern Time.

        week_key: if provided will always return that week
        date_trigger: can either be first_game or last_game. used to compare
            with current time
        delay: delay by one week

        By default this method returns the upcoming week. Sometimes you might
        want a page displaying previous week's results, so you might want to
        delay the week returned so you show last week results longer.
        """
        if week_key:
            return cls.objects.get(pk=week_key)
        return cls._find_current_week(date_trigger, delay)

    @classmethod
    def _find_current_week(cls, date_trigger, delay):
        assert date_trigger in ("first_game", "last_game")
        current_time = tz.get_current_time()

        current_week = None
        season_weeks = cls.active_weeks()
        for cnt, week in enumerate(season_weeks):
            current_week = season_weeks[cnt - 1] if delay and cnt > 0 else week
            if current_time < getattr(week, date_trigger).replace(tzinfo=tz.EASTERN):
                break
        return current_week


class Game(TimestampMixin):
    """
    Individual Game Matchup
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
        ordering = ['game_time']

    def __unicode__(self):
        return "%s vs. %s" % (self.home_id, self.away_id)
    
    def save(self, **kwargs):
        self.primary_key = "%s-%s" % (self.week.pk, self.number)
        super(Game, self).save(**kwargs)