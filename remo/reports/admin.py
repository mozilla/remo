from django.contrib import admin

from import_export import fields, resources
from import_export.admin import ExportMixin

from remo.reports.models import Activity, Campaign, NGReport, NGReportComment


class NGReportCommentInline(admin.StackedInline):
    """NGReportComment Inline."""
    model = NGReportComment
    extra = 1


class NGReportResource(resources.ModelResource):
    user = fields.Field(column_name='user')
    mentor = fields.Field(column_name='mentor')

    class Meta:
        model = NGReport
        fields = ('user', 'report_date', 'mentor', 'activity', 'campaign', 'functional_areas',
                  'location', 'country', 'is_passive', 'event', 'activity_description',
                  'verified_activity', 'link', 'link_description',)

    def dehydrate_user(self, ngreport):
        return ngreport.user.get_full_name()

    def dehydrate_mentor(self, ngreport):
        if ngreport.mentor:
            return ngreport.mentor.get_full_name()
        return ''

    def dehydrate_campaign(self, ngreport):
        if ngreport.campaign:
            return ngreport.campaign.name
        return ''

    def dehydrate_activity(self, ngreport):
        if ngreport.activity:
            return ngreport.activity.name
        return ''

    def dehydrate_functional_areas(self, ngreport):
        if ngreport.functional_areas.all().exists():
            functional_areas = ', '.join([x.name for x in ngreport.functional_areas.all()])
            return functional_areas
        return ''

    def dehydrate_event(self, ngreport):
        if ngreport.event:
            return ngreport.event.name
        return ''


class NGReportAdmin(ExportMixin, admin.ModelAdmin):
    """New Generation Report Admin."""
    resource_class = NGReportResource
    inlines = [NGReportCommentInline]

    list_display = ('user', 'report_date', 'created_on', 'updated_on')
    search_fields = ['user__first_name', 'user__last_name',
                     'user__userprofile__display_name', 'activity__name',
                     'campaign__name']
    list_filter = ['activity__name', 'campaign__name']


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
