from django.contrib import admin

from models import Attendance, Event, EventGoal, Metric


class AttendanceInline(admin.StackedInline):
    """Attendance Inline."""
    model = Attendance


class MetricInline(admin.StackedInline):
    """Metric Inline."""
    model = Metric


class EventGoalAdmin(admin.ModelAdmin):
    """Metric Inline."""
    model = EventGoal


class EventAdmin(admin.ModelAdmin):
    """Event Admin."""
    inlines = [AttendanceInline, MetricInline]
    model = Event
    list_display = ('name', 'start', 'end')
    search_fields = ('name', 'country', 'region', 'venue')

    def owner_display_name(self, obj):
        return obj.owner.userprofile.display_name


admin.site.register(Event, EventAdmin)
admin.site.register(EventGoal, EventGoalAdmin)
