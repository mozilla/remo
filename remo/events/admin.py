from django.contrib import admin

from import_export.admin import ExportMixin
from models import (Attendance, Event, EventGoal, EventMetric,
                    EventMetricOutcome)


class AttendanceInline(admin.StackedInline):
    """Attendance Inline."""
    model = Attendance


class EventGoalAdmin(ExportMixin, admin.ModelAdmin):
    """EventGoal Inline."""
    model = EventGoal


class EventAdmin(ExportMixin, admin.ModelAdmin):
    """Event Admin."""
    inlines = [AttendanceInline]
    model = Event
    list_display = ('name', 'start', 'end')
    search_fields = ('name', 'country', 'region', 'venue')

    def owner_display_name(self, obj):
        return obj.owner.userprofile.display_name


class EventMetricAdmin(ExportMixin, admin.ModelAdmin):
    """EventMetric Admin."""
    model = EventMetric
    list_display = ('name', 'active')
    list_filter = ('active',)


class EventMetricOutcomeAdmin(ExportMixin, admin.ModelAdmin):
    """EventMetricOutcome Admin."""
    model = EventMetricOutcome
    list_display = ('event', 'metric', 'expected_outcome')

admin.site.register(Event, EventAdmin)
admin.site.register(EventGoal, EventGoalAdmin)
admin.site.register(EventMetric, EventMetricAdmin)
admin.site.register(EventMetricOutcome, EventMetricOutcomeAdmin)
