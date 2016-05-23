from django.contrib import admin
from django.utils.encoding import smart_text

from import_export.admin import ExportMixin

from remo.remozilla.models import Bug, Status


def encode_bugzilla_strings(modeladmin, request, queryset):
    for obj in queryset:
        kwargs = {}
        fields = ['component', 'summary', 'whiteboard', 'status', 'resolution', 'first_comment']
        for field in fields:
            kwargs[field] = smart_text(getattr(obj, field))
        Bug.objects.filter(pk=obj.id).update(**kwargs)

encode_bugzilla_strings.short_description = 'Encode bugzilla strings'


class BugAdmin(ExportMixin, admin.ModelAdmin):
    """Bug Admin."""
    list_display = ('__unicode__', 'summary', 'status', 'resolution',
                    'bug_last_change_time',)
    list_filter = ('status', 'resolution', 'council_vote_requested',)
    search_fields = ('bug_id', 'summary', 'id',)
    actions = [encode_bugzilla_strings]

admin.site.register(Bug, BugAdmin)
admin.site.register(Status)
