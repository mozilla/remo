from django.contrib import admin

from import_export import fields, resources
from import_export.admin import ExportMixin

from remo.featuredrep.models import FeaturedRep


class FeaturedRepResource(resources.ModelResource):
    user = fields.Field()

    class Meta:
        model = FeaturedRep

    def dehydrate_users(self, featuredrep):
        return featuredrep.users.all()


class FeaturedRepAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = FeaturedRepResource
    model = FeaturedRep
    list_display = ('featured_rep_users', 'created_on')
    search_fields = ['users__first_name', 'users__last_name']

    def featured_rep_users(self, obj):
        return ', '.join([user.get_full_name() for user in obj.users.all()])


admin.site.register(FeaturedRep, FeaturedRepAdmin)
