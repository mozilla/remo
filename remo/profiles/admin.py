from socket import error as socket_error

from django.conf.urls import patterns, url
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from import_export import fields, resources
from import_export.admin import ExportMixin
from functools import update_wrapper

from remo.profiles.models import (FunctionalArea, UserAvatar, UserProfile,
                                  UserStatus)
from remo.profiles.tasks import check_celery

# Unregister User from Administration to attach UserProfileInline
admin.site.unregister(User)


class UserProfileInline(admin.StackedInline):
    """ReportLink Inline."""
    model = UserProfile
    fk_name = 'user'


class UserAdmin(ExportMixin, UserAdmin):
    """User Admin."""
    inlines = [UserProfileInline]

    def get_urls(self):
        """Return custom and UserAdmin urls."""

        def wrap(view):

            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        urls = super(UserAdmin, self).get_urls()
        my_urls = patterns('', url(r'check_celery', wrap(self.check_celery),
                                   name='users_check_celery'))
        return my_urls + urls

    def check_celery(self, request):
        try:
            investigator = check_celery.delay()
        except socket_error as e:
            messages.error(request, 'Cannot connect to broker: %s' % e)
            return HttpResponseRedirect(reverse('admin:auth_user_changelist'))

        try:
            investigator.get(timeout=5)
        except investigator.TimeoutError as e:
            messages.error(request, 'Worker timeout: %s' % e)
        else:
            messages.success(request, 'Celery is OK')
        finally:
            return HttpResponseRedirect(reverse('admin:auth_user_changelist'))


class UserAvatarResource(resources.ModelResource):
    user = fields.Field()

    class Meta:
        model = UserAvatar

    def dehydrate_user(self, useravatar):
        return useravatar.user.get_full_name()


class UserAvatarAdmin(ExportMixin, admin.ModelAdmin):
    """UserAvatar Admin."""
    resource_class = UserAvatarResource
    list_display = ('display_name', 'avatar_url', 'last_update')

    def display_name(self, obj):
        return obj.user.userprofile.display_name


class FunctionalAreaAdmin(ExportMixin, admin.ModelAdmin):
    """FunctionalArea Admin."""
    list_display = ('name', 'registered_reps', 'registered_mozillians',
                    'registered_events', 'active')

    def registered_reps(self, obj):
        return obj.users_matching.count()

    def registered_mozillians(self, obj):
        return obj.users_tracking.count()

    def registered_events(self, obj):
        return obj.events_categories.count()

    def queryset(self, request):
        return self.model.objects.get_query_set()


class UserStatusResource(resources.ModelResource):
    user = fields.Field()
    replacement_rep = fields.Field()

    class Meta:
        model = UserStatus

    def dehydrate_user(self, userstatus):
        return userstatus.user.get_full_name()

    def dehydrate_replacement_rep(self, userstatus):
        if userstatus.replacement_rep:
            return userstatus.replacement_rep.get_full_name()
        return None


class UserStatusAdmin(ExportMixin, admin.ModelAdmin):
    """User Status Admin."""
    resource_class = UserStatusResource
    model = UserStatus
    list_display = ('user', 'expected_date', 'return_date', 'created_on',
                    'replacement_rep')
    search_fields = ['user__first_name', 'user__last_name',
                     'user__userprofile__display_name']


admin.site.register(User, UserAdmin)
admin.site.register(FunctionalArea, FunctionalAreaAdmin)
admin.site.register(UserAvatar, UserAvatarAdmin)
admin.site.register(UserStatus, UserStatusAdmin)
