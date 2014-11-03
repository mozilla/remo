from django.contrib import admin

from import_export.admin import ExportMixin
from remo.remozilla.models import Bug, Status


class BugAdmin(ExportMixin, admin.ModelAdmin):
    """Bug Admin."""
    list_display = ('__unicode__', 'summary', 'status', 'resolution',
                    'bug_last_change_time',)
    list_filter = ('status', 'resolution', 'council_vote_requested',)
    search_fields = ('bug_id', 'summary', 'id',)

admin.site.register(Bug, BugAdmin)
admin.site.register(Status)
