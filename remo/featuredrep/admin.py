from django.contrib import admin

from import_export import fields, resources
from import_export.admin import ExportMixin

from remo.featuredrep.models import FeaturedRep


class FeaturedRepResource(resources.ModelResource):
    user = fields.Field()

    class Meta:
        model = FeaturedRep

    def dehydrate_user(self, featuredrep):
        return featuredrep.user.get_full_name()


class FeaturedRepAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = FeaturedRepResource
    model = FeaturedRep
    list_display = ('user', 'created_on')
    search_fields = ['user__first_name', 'user__last_name',
                     'user__userprofile__display_name']


admin.site.register(FeaturedRep, FeaturedRepAdmin)
