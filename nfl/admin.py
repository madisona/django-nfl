
from django.contrib import admin

from nfl import models

class DivisionAdmin(admin.ModelAdmin):
    readonly_fields = ['conference', 'region']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'abbr', 'division', 'is_active']
    list_filter = ['division', 'is_active']

class WeekAdmin(admin.ModelAdmin):
    list_display = ['number', 'first_game', 'last_game']
    list_filter = ['season__year']

class GameAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'week_pk', 'number', 'game_time']
    list_filter = ['week__season__year', 'week__number', 'game_time']
    date_hierarchy = 'game_time'

    def week_pk(self, obj):
        return obj.week.pk
    week_pk.short_description = "Week Number"

class WinnerAdmin(admin.ModelAdmin):
    fields = ('week',
        'game1', 'game2', 'game3', 'game4',
        'game5', 'game6', 'game7', 'game8',
        'game9', 'game10', 'game11', 'game12',
        'game13', 'game14', 'game15', 'game16',
    )
    list_filter = ['week__season__year']

class TeamResultAdmin(admin.ModelAdmin):
    list_filter = ('week', 'week__season__year')
    fields = ('week', 'team', 'wins', 'losses', 'total_wins', 'total_losses')

admin.site.register(models.Division, DivisionAdmin)
admin.site.register(models.Season)
admin.site.register(models.Team, TeamAdmin)
admin.site.register(models.Week, WeekAdmin)
admin.site.register(models.Game, GameAdmin)

admin.site.register(models.Winner, WinnerAdmin)
admin.site.register(models.TeamResult, TeamResultAdmin)