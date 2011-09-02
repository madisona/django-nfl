
import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from nfl import models

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

    def test_gets_by_season(self):
        old_season = models.Season.objects.create(year="2010")
        season = models.Season.objects.create(year="2011")
        today = datetime.datetime.today()
        current_week = models.Week.objects.create(number=1, season=season, first_game=today, last_game=today)
        models.Week.objects.create(number=1, season=old_season, first_game=today, last_game=today)

        weeks = models.Week.get_by_season(season)
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

#    def test_returns_current_week_when_week_key_give(self):
#        season = self.make_active_season()
#        today = datetime.datetime.now()
#        key = "2011-1"
#        week = models.Week.objects.create(season=season, number=1, first_game=today, last_game=today, appengine_key=key)
#
#        current_week = models.Week.objects.get_current_week(key)
#        self.assertEqual(week, current_week)
#
#    def test_returns_current_week_when_before_first_week(self):
#        season = self.make_active_season()
#        today = get_current_time()
#        tomorrow = today + datetime.timedelta(days=1)
#        next_week = tomorrow + datetime.timedelta(days=7)
#
#        week1 = models.Week.objects.create(number=1, first_game=tomorrow, last_game=tomorrow, season=season)
#        models.Week.objects.create(number=2, first_game=next_week, last_game=next_week, season=season)
#
#        current_week = models.Week.objects.get_current_week(None, datetype="first_game")
#        self.assertEqual(week1, current_week)
#
#    def test_finds_current_week_by_first_game(self):
#        season = self.make_active_season()
#        today = get_current_time()
#        yesterday = today - datetime.timedelta(days=1)
#        next_week = today + datetime.timedelta(days=7)
#        two_weeks = today + datetime.timedelta(days=14)
#
#        models.Week.objects.create(number=1, first_game=yesterday, last_game=yesterday, season=season)
#        week = models.Week.objects.create(number=2, first_game=next_week, last_game=next_week, season=season)
#        models.Week.objects.create(number=3, first_game=two_weeks, last_game=two_weeks, season=season)
#
#        current_week = models.Week.objects.get_current_week(None, datetype="first_game")
#        self.assertEqual(week, current_week)
#
#    def test_finds_current_week_by_last_game(self):
#        season = self.make_active_season()
#        today = get_current_time()
#        yesterday = today - datetime.timedelta(days=1)
#        next_week = today + datetime.timedelta(days=7)
#        two_weeks = today + datetime.timedelta(days=14)
#
#        models.Week.objects.create(number=1, first_game=yesterday, last_game=yesterday, season=season)
#        week = models.Week.objects.create(number=2, first_game=yesterday, last_game=next_week, season=season)
#        models.Week.objects.create(number=3, first_game=two_weeks, last_game=two_weeks, season=season)
#
#        current_week = models.Week.objects.get_current_week(None, datetype="last_game")
#        self.assertEqual(week, current_week)
#
#    def test_returns_last_season_week_when_time_after_all_weeks(self):
#        season = self.make_active_season()
#        today = get_current_time()
#        yesterday = today - datetime.timedelta(days=1)
#        last_week = today - datetime.timedelta(days=7)
#
#        models.Week.objects.create(number=1, first_game=last_week, last_game=last_week, season=season)
#        week = models.Week.objects.create(number=2, first_game=yesterday, last_game=yesterday, season=season)
#
#        current_week = models.Week.objects.get_current_week(None)
#        self.assertEqual(week, current_week)
#
#    def test_returns_one_week_behind_when_delay_flag_set(self):
#        season = self.make_active_season()
#        today = get_current_time()
#        yesterday = today - datetime.timedelta(days=1)
#        next_week = today + datetime.timedelta(days=7)
#
#        week = models.Week.objects.create(number=1, first_game=yesterday, last_game=yesterday, season=season)
#        models.Week.objects.create(number=2, first_game=next_week, last_game=next_week, season=season)
#
#        current_week = models.Week.objects.get_current_week(None, delay=True)
#        self.assertEqual(week, current_week)

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
        