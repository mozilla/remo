from django.contrib import admin

from remo.reports.models import Report, ReportComment, ReportEvent, ReportLink


class ReportLinkInline(admin.StackedInline):
    """ReportLink Inline."""
    model = ReportLink


class ReportEventInline(admin.StackedInline):
    """ReportEvent Inline."""
    model = ReportEvent


class ReportCommentInline(admin.StackedInline):
    """ReportComment Inline."""
    model = ReportComment


class ReportAdmin(admin.ModelAdmin):
    """Report Admin."""
    inlines = [ReportLinkInline, ReportEventInline, ReportCommentInline]
    list_display = ('__unicode__', 'display_name')

    def display_name(self, obj):
        return obj.user.userprofile.display_name


admin.site.register(Report, ReportAdmin)
