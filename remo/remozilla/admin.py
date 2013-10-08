from django.contrib import admin

from remo.remozilla.models import Bug, Status


class BugAdmin(admin.ModelAdmin):
    """Bug Admin."""
    list_display = ('__unicode__', 'summary', 'status', 'resolution')
    list_filter = ('status', 'resolution', 'council_vote_requested')
    search_fields = ('bug_id',)


admin.site.register(Bug, BugAdmin)
admin.site.register(Status)
