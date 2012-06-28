from django.contrib import admin

from remo.remozilla.models import Bug, Status


class BugAdmin(admin.ModelAdmin):
    """Bug Admin."""
    list_display = ('__unicode__', 'summary', 'status', 'resolution')
    list_filter = ('status', 'resolution')


admin.site.register(Bug, BugAdmin)
admin.site.register(Status)
