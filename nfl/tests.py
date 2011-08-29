
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
        all_teams_count = models.Team.all_teams().count()
        self.assertEqual(32, all_teams_count)
