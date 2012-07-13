from django.contrib import admin

from models import Attendance, Metric, Event


class AttendanceInline(admin.StackedInline):
    """Attendance Inline."""
    model = Attendance


class MetricInline(admin.StackedInline):
    """Metric Inline."""
    model = Metric


class EventAdmin(admin.ModelAdmin):
    """Event Admin."""
    inlines = [MetricInline, AttendanceInline]
    model = Event
    list_display = ('name', 'start', 'end')
    search_fields = ('name', 'country', 'region', 'venue')

    def owner_display_name(self, obj):
        return obj.owner.userprofile.display_name


admin.site.register(Event, EventAdmin)
