from django.contrib import admin

from models import (Attendance, Event, EventGoal, EventMetric,
                    EventMetricOutcome)


class AttendanceInline(admin.StackedInline):
    """Attendance Inline."""
    model = Attendance


class EventGoalAdmin(admin.ModelAdmin):
    """EventGoal Inline."""
    model = EventGoal


class EventAdmin(admin.ModelAdmin):
    """Event Admin."""
    inlines = [AttendanceInline]
    model = Event
    list_display = ('name', 'start', 'end')
    search_fields = ('name', 'country', 'region', 'venue')

    def owner_display_name(self, obj):
        return obj.owner.userprofile.display_name


class EventMetricAdmin(admin.ModelAdmin):
    """EventMetric Admin."""
    model = EventMetric
    list_display = ('name', 'active')
    list_filter = ('active',)


class EventMetricOutcomeAdmin(admin.ModelAdmin):
    """EventMetricOutcome Admin."""
    model = EventMetricOutcome
    list_display = ('event', 'metric', 'expected_outcome')

admin.site.register(Event, EventAdmin)
admin.site.register(EventGoal, EventGoalAdmin)
admin.site.register(EventMetric, EventMetricAdmin)
admin.site.register(EventMetricOutcome, EventMetricOutcomeAdmin)
