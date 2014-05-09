from django.contrib import admin

from models import Attendance, Event, EventGoal
from import_export.admin import ExportMixin


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


admin.site.register(Event, EventAdmin)
admin.site.register(EventGoal, EventGoalAdmin)
