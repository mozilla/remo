from django.contrib import admin

from import_export import fields, resources
from import_export.admin import ExportMixin
from models import (Attendance, Event, EventGoal, EventMetric,
                    EventMetricOutcome)


class AttendanceInline(admin.StackedInline):
    """Attendance Inline."""
    model = Attendance


class EventGoalAdmin(ExportMixin, admin.ModelAdmin):
    """EventGoal Inline."""
    model = EventGoal


class EventResource(resources.ModelResource):
    event_goals = fields.Field()
    event_categories = fields.Field()
    event_metrics = fields.Field()

    class Meta:
        model = Event
        exclude = ('id', 'categories', 'goals', 'metrics',)

    def dehydrate_event_goals(self, event):
        if event.goals.all().exists():
            goals = ', '.join(x.name for x in event.goals.all())
            return goals
        return ''

    def dehydrate_event_categories(self, event):
        if event.categories.all().exists():
            categories = ', '.join([x.name for x in event.categories.all()])
            return categories
        return ''

    def dehydrate_event_metrics(self, event):
        event_metrics = event.metrics.all()
        if event_metrics.exists():
            event_outcome = EventMetricOutcome.objects.filter(event=event)
            if event_outcome.exists():
                outcome = [(x.metric.name, x.expected_outcome, x.outcome)
                           for x in event_outcome]
                return str(outcome).strip('[]')
            else:
                metrics = ', '.join(x.name for x in event_metrics)
            return metrics
        return ''


class EventAdmin(ExportMixin, admin.ModelAdmin):
    """Event Admin."""
    resource_class = EventResource
    inlines = [AttendanceInline]
    model = Event
    list_display = ('name', 'start', 'end')
    search_fields = ('name', 'country', 'region', 'venue', 'slug')

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
    list_display = ('event', 'metric', 'expected_outcome', 'outcome')
    search_fields = ('event__name', 'metric__name')

admin.site.register(Event, EventAdmin)
admin.site.register(EventGoal, EventGoalAdmin)
admin.site.register(EventMetric, EventMetricAdmin)
admin.site.register(EventMetricOutcome, EventMetricOutcomeAdmin)
