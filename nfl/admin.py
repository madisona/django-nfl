
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

admin.site.register(models.Division, DivisionAdmin)
admin.site.register(models.Season)
admin.site.register(models.Team, TeamAdmin)
admin.site.register(models.Week, WeekAdmin)
admin.site.register(models.Game, GameAdmin)