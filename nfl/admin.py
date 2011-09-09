
from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.admin.options import csrf_protect_m
from django.contrib.admin.util import unquote
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.utils.encoding import force_unicode
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from nfl import models, forms

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
    form = forms.BaseGamesForm

    def get_admin_form(self, form, request, obj=None):
        return helpers.AdminForm(form, list(self.get_fieldsets(request, obj)),
                                 self.prepopulated_fields, self.get_readonly_fields(request, obj),
                                 model_admin=self)

    @csrf_protect_m
    @transaction.commit_on_success
    def add_view(self, request, form_url='', extra_context=None):
        opts = self.model._meta

        if not self.has_add_permission(request):
            raise PermissionDenied

        ModelForm = self.get_form(request)
        form = ModelForm(**self.get_form_kwargs(request))
        if form.is_valid():
            return self.form_valid_add(form, request)

        adminForm = self.get_admin_form(form, request)
        context = {
            'title': _('Add %s') % force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'is_popup': "_popup" in request.REQUEST,
            'show_delete': False,
            'media': mark_safe(self.media + adminForm.media),
            'inline_admin_formsets': [],
            'errors': helpers.AdminErrorList(form, []),
            'root_path': self.admin_site.root_path,
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, form_url=form_url, add=True)

    def get_form_kwargs(self, request):
        return {
            'initial': self.get_initial(request),
            'data': request.POST or None,
            'files': request.FILES or None,
        }

    def get_initial(self, request):
        return dict(request.GET.items())

    def form_valid_add(self, form, request):
        new_object = form.save()
        self.log_addition(request, new_object)
        return self.response_add(request, new_object)

    def form_valid_change(self, form, request):
        new_object = form.save()
        change_message = self.construct_change_message(request, form, [])
        self.log_change(request, new_object, change_message)
        return self.response_change(request, new_object)

    @csrf_protect_m
    @transaction.commit_on_success
    def change_view(self, request, object_id, extra_context=None):
        opts = self.model._meta
        obj = self.get_object(request, unquote(object_id))

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})

        if request.method == 'POST' and "_saveasnew" in request.POST:
            return self.add_view(request, form_url='../add/')

        ModelForm = self.get_form(request, obj)

        form = ModelForm(request.POST or None, request.FILES or None, instance=obj)
        if form.is_valid():
            return self.form_valid_change(form, request)

        adminForm = self.get_admin_form(form, request, obj)
        context = {
            'title': _('Change %s') % force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'object_id': object_id,
            'original': obj,
            'is_popup': "_popup" in request.REQUEST,
            'media': mark_safe(self.media + adminForm.media),
            'inline_admin_formsets': [],
            'errors': helpers.AdminErrorList(form, []),
            'root_path': self.admin_site.root_path,
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, change=True, obj=obj)


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