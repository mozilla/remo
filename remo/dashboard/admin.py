from django.contrib import admin

from import_export.admin import ExportMixin

from remo.dashboard.models import ActionItem


class ActionItemAdmin(ExportMixin, admin.ModelAdmin):
    model = ActionItem

    list_display = ('__unicode__', 'user', 'due_date', 'created_on',
                    'priority', 'updated_on')
    search_fields = ['user__first_name', 'user__last_name',
                     'user__userprofile__display_name', 'name']


admin.site.register(ActionItem, ActionItemAdmin)
