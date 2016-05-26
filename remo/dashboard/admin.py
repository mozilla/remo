from django.contrib import admin
from django.utils.encoding import smart_text

from import_export.admin import ExportMixin

from remo.dashboard.models import ActionItem


def encode_action_item_names(modeladmin, request, queryset):
    for obj in queryset:
        ActionItem.objects.filter(pk=obj.id).update(name=smart_text(obj.name))

encode_action_item_names.short_description = 'Encode action item names'


class ActionItemAdmin(ExportMixin, admin.ModelAdmin):
    model = ActionItem

    list_display = ('__unicode__', 'user', 'due_date', 'created_on',
                    'priority', 'updated_on', 'object_id',)
    search_fields = ['user__first_name', 'user__last_name',
                     'user__userprofile__display_name', 'name']
    actions = [encode_action_item_names]


admin.site.register(ActionItem, ActionItemAdmin)
