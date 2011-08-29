
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

admin.site.register(models.Division, DivisionAdmin)
admin.site.register(models.Season)
admin.site.register(models.Team, TeamAdmin)