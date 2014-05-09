from django.contrib import admin

from import_export import fields, resources
from import_export.admin import ExportMixin

from remo.reports.models import Activity, Campaign, NGReport, NGReportComment


class NGReportCommentInline(admin.StackedInline):
    """NGReportComment Inline."""
    model = NGReportComment
    extra = 1


class NGReportResource(resources.ModelResource):
    user = fields.Field()

    class Meta:
        model = NGReport

    def dehydrate_user(self, ngreport):
        return ngreport.user.get_full_name()


class NGReportAdmin(ExportMixin, admin.ModelAdmin):
    """New Generation Report Admin."""
    resource_class = NGReportResource
    inlines = [NGReportCommentInline]
    list_display = ('user', 'report_date', 'created_on', 'updated_on')
    search_fields = ['user__first_name', 'user__last_name',
                     'user__userprofile__display_name']


class ActivityAdmin(ExportMixin, admin.ModelAdmin):
    """Activity Admin."""
    model = Activity
    list_display = ('__unicode__', 'active')
    list_filter = ('active',)


class CampaignAdmin(ExportMixin, admin.ModelAdmin):
    """Campaign Admin."""
    model = Campaign
    list_display = ('__unicode__', 'active')
    list_filter = ('active',)


admin.site.register(NGReport, NGReportAdmin)
admin.site.register(Activity, ActivityAdmin)
admin.site.register(Campaign, CampaignAdmin)
