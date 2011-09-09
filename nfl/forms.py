
from django import forms
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe

from nfl import models


class ScheduleGameWidget(forms.RadioSelect.renderer):

    def render(self):
        """Outputs a <ul> for this set of radio fields."""
        return mark_safe(u'<ul class="radiolist inline">%s</ul>' % u''.join([u'<li>%s</li>'
                % force_unicode(w) for w in self]))

class BaseGamesForm(forms.ModelForm):
    date_trigger = 'first_game'
    delay = False

    def __init__(self, *args,  **kwargs):
        self.current_week_key = kwargs.pop('current_week', None)


        super(BaseGamesForm, self).__init__(*args, **kwargs)
        self.add_game_fields()

    def add_game_fields(self):
        """
        Adds all the games. It is WAY more efficient to just get the values
        for the games and look up the team numbers than to let the foreign
        keys just do all their lookups. (8 rpc's vs ~ 38)
        """
        current_week = models.Week.current_week(self.initial.get('week'),
                                                self.date_trigger, self.delay)

        teams = dict((t.pk, t) for t in models.Team.all_teams())
        for game in models.Game.week_schedule(current_week):
            away_team = teams.get(game.away_id)
            home_team = teams.get(game.home_id)

            # if we don't add the field name to _meta.fields, the games
            # won't save when the form saves.
            field_name = 'game%s' % game.number
            self._meta.fields.append(field_name)
            self.fields[field_name] = forms.ChoiceField(
                label='Game %s' % game.number,
                widget=self.get_game_choice_widget(),
                choices=[
                    (game.away_id, self._get_label(away_team)),
                    (game.home_id, self._get_label(home_team)),                                                            ],
                )

    def get_game_choice_widget(self):
        return forms.RadioSelect(renderer=ScheduleGameWidget)

    def _get_label(self, team):
        return str(team)
#        return "%s (%s-%s)" % (team, team.wins, team.losses)