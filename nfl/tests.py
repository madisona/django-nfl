
import datetime

from django.core.exceptions import ValidationError
from django.core.cache import get_cache, cache
from django.test import TestCase

from nfl import models, tz
from nfl import utils

class SeasonModelTests(TestCase):

    def test_returns_active_season(self):
        models.Season.objects.create(year='2010', is_active=False)
        season = models.Season.objects.create(year='2011', is_active=True)

        active_season = models.Season.active_season()
        self.assertEqual(season, active_season)

    def test_returns_year_as_string_representation(self):
        season = models.Season(year="2011")
        self.assertEqual("2011", str(season))

    def test_doesnt_allow_characters_in_year(self):
        season = models.Season(year="abcd")
        with self.assertRaises(ValidationError):
            season.full_clean()

    def test_doesnt_allow_less_than_four_digit_year(self):
        season = models.Season(year="201")
        with self.assertRaises(ValidationError):
            season.full_clean()

    def test_doesnt_allow_more_than_four_digit_year(self):
        season = models.Season(year="20111")
        with self.assertRaises(ValidationError):
            season.full_clean()

    def test_allows_four_digit_year(self):
        season = models.Season(year="2011")
        self.assertEqual(None, season.full_clean())

    def test_allows_only_one_active_season(self):
        models.Season.objects.create(year='2009', is_active=True)
        season = models.Season.objects.create(year='2010', is_active=True)
        models.Season.objects.create(year='2011', is_active=False)

        active_season = models.Season.active_season()
        self.assertEqual(season, active_season)

class DivisionModelTests(TestCase):

    def test_uses_conference_and_region_as_pk(self):
        division = models.Division.objects.get(conference="AFC", region="East")
        self.assertEqual("AFC-East", division.pk)

class TeamModelTests(TestCase):

    def test_uses_abbr_as_primary_key(self):
        """
        Teams are in initial data and pk is abbreviation.
        """
        team = models.Team.objects.get(pk="BUF")
        self.assertEqual("Buffalo", team.name)

    def test_uses_name_as_string_representation(self):
        team = models.Team.objects.get(pk="BUF")
        self.assertEqual("Buffalo", str(team))

    def test_all_teams_returns_all_active_teams(self):
        division = models.Division.objects.get(pk="AFC-East")
        models.Team.objects.create(pk="XYZ", name="Fake Team", is_active=False, division=division)
        all_teams_count = len(models.Team.all_teams())
        self.assertEqual(32, all_teams_count)

class WeekModelTests(TestCase):

    def test_gets_season_weeks(self):
        old_season = models.Season.objects.create(year="2010")
        season = models.Season.objects.create(year="2011")
        today = datetime.datetime.today()
        current_week = models.Week.objects.create(number=1, season=season, first_game=today, last_game=today)
        models.Week.objects.create(number=1, season=old_season, first_game=today, last_game=today)

        weeks = models.Week.season_weeks(season)
        self.assertEqual([current_week], list(weeks))

    def test_gets_active_season_weeks(self):
        old_season = models.Season.objects.create(year="2010")
        season = models.Season.objects.create(year="2011", is_active=True)
        today = datetime.datetime.today()
        current_week = models.Week.objects.create(number=1, season=season, first_game=today, last_game=today)
        models.Week.objects.create(number=1, season=old_season, first_game=today, last_game=today)

        weeks = models.Week.active_weeks()
        self.assertEqual([current_week], list(weeks))

    def test_uses_season_key_and_number_as_primary_key(self):
        today = datetime.datetime.today()
        season = models.Season.objects.create(year="2011")
        week = models.Week.objects.create(season=season, number=1, first_game=today, last_game=today)
        self.assertEqual("2011-1", week.primary_key)

    def test_doesnt_allow_week_number_less_than_one(self):
        season = models.Season.objects.create(year="2011")
        today = datetime.datetime.now()
        week = models.Week(season=season, number=0, first_game=today, last_game=today)
        with self.assertRaises(ValidationError) as e:
            week.full_clean()
        self.assertEqual("Ensure this value is greater than or equal to 1.", e.exception.messages[0])

    def test_doesnt_allow_week_number_greater_than_twenty_one(self):
        season = models.Season.objects.create(year="2011")
        today = datetime.datetime.now()
        week = models.Week(season=season, number=22, first_game=today, last_game=today)
        with self.assertRaises(ValidationError) as e:
            week.full_clean()
        self.assertEqual("Ensure this value is less than or equal to 21.", e.exception.messages[0])

    def test_current_week_returns_week_specified_when_week_key_give(self):
        season = models.Season.objects.create(year="2011")
        today = datetime.datetime.now()
        key = "2011-1"
        week = models.Week.objects.create(season=season, number=1, first_game=today, last_game=today)

        current_week = models.Week.current_week(key)
        self.assertEqual(week, current_week)

    def test_current_week_returns_week_one_when_before_first_week(self):
        season = models.Season.objects.create(year="2011", is_active=True)

        today = tz.get_current_time()
        tomorrow = today + datetime.timedelta(days=1)
        next_week = tomorrow + datetime.timedelta(days=7)

        week1 = models.Week.objects.create(number=1, first_game=tomorrow, last_game=tomorrow, season=season)
        models.Week.objects.create(number=2, first_game=next_week, last_game=next_week, season=season)

        current_week = models.Week.current_week(date_trigger="first_game")
        self.assertEqual(week1, current_week)

    def test_finds_current_week_by_first_game(self):
        season = models.Season.objects.create(year="2011", is_active=True)
        today = tz.get_current_time()
        yesterday = today - datetime.timedelta(days=1)
        next_week = today + datetime.timedelta(days=7)
        two_weeks = today + datetime.timedelta(days=14)

        models.Week.objects.create(number=1, first_game=yesterday, last_game=yesterday, season=season)
        week = models.Week.objects.create(number=2, first_game=next_week, last_game=next_week, season=season)
        models.Week.objects.create(number=3, first_game=two_weeks, last_game=two_weeks, season=season)

        current_week = models.Week.current_week(date_trigger="first_game")
        self.assertEqual(week, current_week)

    def test_finds_current_week_by_last_game(self):
        season = models.Season.objects.create(year="2011", is_active=True)
        today = tz.get_current_time()
        yesterday = today - datetime.timedelta(days=1)
        next_week = today + datetime.timedelta(days=7)
        two_weeks = today + datetime.timedelta(days=14)

        models.Week.objects.create(number=1, first_game=yesterday, last_game=yesterday, season=season)
        week = models.Week.objects.create(number=2, first_game=yesterday, last_game=next_week, season=season)
        models.Week.objects.create(number=3, first_game=two_weeks, last_game=two_weeks, season=season)

        current_week = models.Week.current_week(date_trigger="last_game")
        self.assertEqual(week, current_week)

    def test_returns_last_season_week_when_time_after_all_weeks(self):
        season = models.Season.objects.create(year="2011", is_active=True)
        today = tz.get_current_time()
        yesterday = today - datetime.timedelta(days=1)
        last_week = today - datetime.timedelta(days=7)

        models.Week.objects.create(number=1, first_game=last_week, last_game=last_week, season=season)
        week = models.Week.objects.create(number=2, first_game=yesterday, last_game=yesterday, season=season)

        current_week = models.Week.current_week()
        self.assertEqual(week, current_week)

    def test_returns_one_week_behind_when_delay_flag_set(self):
        season = models.Season.objects.create(year="2011", is_active=True)
        today = tz.get_current_time()
        yesterday = today - datetime.timedelta(days=1)
        next_week = today + datetime.timedelta(days=7)

        week = models.Week.objects.create(number=1, first_game=yesterday, last_game=yesterday, season=season)
        models.Week.objects.create(number=2, first_game=next_week, last_game=next_week, season=season)

        current_week = models.Week.current_week(delay=True)
        self.assertEqual(week, current_week)

class GameModelTests(TestCase):

    def setUp(self):
        self.today = datetime.datetime.now()
        self.team = models.Team.objects.get(pk="BUF")
        self.season = models.Season.objects.create(year="2011")
        self.week = models.Week.objects.create(season=self.season, number=1, first_game=self.today, last_game=self.today)

    def test_uses_week_key_and_number_as_primary_key(self):
        game = models.Game.objects.create(week=self.week, number=2, game_time=self.today, home=self.team, away=self.team)
        self.assertEqual("2011-1-2", game.primary_key)

    def test_doesnt_allow_week_number_less_than_one(self):
        game = models.Game(week=self.week, number=0, game_time=self.today, home=self.team, away=self.team)
        with self.assertRaises(ValidationError) as e:
            game.full_clean()
        self.assertEqual("Ensure this value is greater than or equal to 1.", e.exception.messages[0])

    def test_doesnt_allow_week_number_greater_than_sixteen(self):
        game = models.Game(week=self.week, number=17, game_time=self.today, home=self.team, away=self.team)
        with self.assertRaises(ValidationError) as e:
            game.full_clean()
        self.assertEqual("Ensure this value is less than or equal to 16.", e.exception.messages[0])

    def test_week_schedule_returns_games_for_week(self):
        week2 = models.Week.objects.create(season=self.season, number=2, first_game=self.today, last_game=self.today)

        game1 = models.Game.objects.create(week=self.week, number=1, game_time=self.today, home=self.team, away=self.team)
        game2 = models.Game.objects.create(week=self.week, number=2, game_time=self.today, home=self.team, away=self.team)
        models.Game.objects.create(week=week2, number=1, game_time=self.today, home=self.team, away=self.team)

        self.assertEqual([game1, game2], models.Game.week_schedule(self.week))

class GameMixinTests(TestCase):

    def test_get_team_returns_team_for_game_number(self):
        game_collection = models.GamesMixin(game1="BUF")
        team = game_collection.get_team(1)
        self.assertTrue(isinstance(team, models.Team))
        self.assertEqual("BUF", team.pk)

    def test_get_team_keeps_teams_dictionary_on_instance(self):
        game_collection = models.GamesMixin(game2="BUF")
        team_dict = dict((t.pk, t) for t in models.Team.all_teams())

        self.assertEqual(None, game_collection.teams)
        game_collection.get_team(2)
        self.assertEqual(team_dict, game_collection.teams)

class ResultMixinTests(TestCase):

    def test_win_percent_returns_value_of_100(self):
        result = models.ResultMixin(total_wins=9, total_losses=1)
        self.assertEqual(90, result.win_percent)

        self.assertEqual(66.67, round(models.ResultMixin(total_wins=2, total_losses=1).win_percent, 2))

    def test_win_percent_returns_none_when_no_wins_or_losses(self):
        result = models.ResultMixin(total_wins=0, total_losses=0)
        self.assertEqual(None, result.win_percent)

class TimeZoneTests(TestCase):

    def test_changes_utc_to_central_standard(self):
        utc_time = datetime.datetime(2011, 3, 12, tzinfo=tz.UTC)
        expected_time = datetime.datetime(2011, 3, 12, tzinfo=tz.CENTRAL) - datetime.timedelta(hours=6)
        self.assertEqual(expected_time, utc_time.astimezone(tz.CENTRAL))

        utc_time = datetime.datetime(2011, 11, 7, tzinfo=tz.UTC)
        expected_time = datetime.datetime(2011, 11, 7, tzinfo=tz.CENTRAL) - datetime.timedelta(hours=6)
        self.assertEqual(expected_time, utc_time.astimezone(tz.CENTRAL))

    def test_changes_utc_to_central_daylight(self):
        utc_time = datetime.datetime(2011, 3, 14, tzinfo=tz.UTC)
        expected_time = datetime.datetime(2011, 3, 14, tzinfo=tz.CENTRAL) - datetime.timedelta(hours=5)
        self.assertEqual(expected_time, utc_time.astimezone(tz.CENTRAL))

        utc_time = datetime.datetime(2011, 11, 5, tzinfo=tz.UTC)
        expected_time = datetime.datetime(2011, 11, 5, tzinfo=tz.CENTRAL) - datetime.timedelta(hours=5)
        self.assertEqual(expected_time, utc_time.astimezone(tz.CENTRAL))

    def test_changes_utc_to_eastern_standard(self):
        utc_time = datetime.datetime(2011, 3, 12, tzinfo=tz.UTC)
        expected_time = datetime.datetime(2011, 3, 12, tzinfo=tz.EASTERN) - datetime.timedelta(hours=5)
        self.assertEqual(expected_time, utc_time.astimezone(tz.EASTERN))

        utc_time = datetime.datetime(2011, 11, 7, tzinfo=tz.UTC)
        expected_time = datetime.datetime(2011, 11, 7, tzinfo=tz.EASTERN) - datetime.timedelta(hours=5)
        self.assertEqual(expected_time, utc_time.astimezone(tz.EASTERN))

    def test_changes_utc_to_eastern_daylight(self):
        utc_time = datetime.datetime(2011, 3, 14, tzinfo=tz.UTC)
        expected_time = datetime.datetime(2011, 3, 14, tzinfo=tz.EASTERN) - datetime.timedelta(hours=4)
        self.assertEqual(expected_time, utc_time.astimezone(tz.EASTERN))

        utc_time = datetime.datetime(2011, 11, 5, tzinfo=tz.UTC)
        expected_time = datetime.datetime(2011, 11, 5, tzinfo=tz.EASTERN) - datetime.timedelta(hours=4)
        self.assertEqual(expected_time, utc_time.astimezone(tz.EASTERN))

    def test_dst_trigger_always_returns_sunday(self):
        sunday = datetime.datetime(2011, 9, 4) # this is a sunday
        dst_trigger = tz.StandardAmericanZone(0, 'Test')._get_next_sunday(sunday)
        self.assertEqual(4, dst_trigger.day)
        self.assertEqual(6, dst_trigger.weekday())

        tuesday = datetime.datetime(2011, 9, 6) # this is a sunday
        dst_trigger = tz.StandardAmericanZone(0, 'Test')._get_next_sunday(tuesday)
        self.assertEqual(11, dst_trigger.day)
        self.assertEqual(6, dst_trigger.weekday())

    def test_dst_trigger_always_returns_sunday_when_getting_next_sunday(self):
        sunday = datetime.datetime(2011, 9, 4) # this is a sunday
        dst_trigger = tz.StandardAmericanZone(0, 'Test')._get_next_sunday(sunday, 7)
        self.assertEqual(11, dst_trigger.day)
        self.assertEqual(6, dst_trigger.weekday())

        tuesday = datetime.datetime(2011, 9, 6) # this is a sunday
        dst_trigger = tz.StandardAmericanZone(0, 'Test')._get_next_sunday(tuesday, 7)
        self.assertEqual(18, dst_trigger.day)
        self.assertEqual(6, dst_trigger.weekday())

class CacheUtilsTests(TestCase):
    """
    This test will fail if you don't have a cache set up in settings.py
    or if you have DummyCache enabled.
    """

    def test_get_or_add_qs_evaluates_list_and_sets_value_when_none_present(self):
        #Test when no value is set
        utils.get_or_add_qs('a','a')
        self.assertEqual(cache.get('a'),['a'])

    def test_get_or_add_qs_returns_value_when_key_already_present(self):
        #Test an existing value
        cache.set('b','b')
        self.assertEqual(utils.get_or_add_qs('b','c'),'b')
