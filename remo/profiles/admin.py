from itertools import izip_longest
from socket import error as socket_error

from django.conf.urls.defaults import patterns, url
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.timezone import now

import csv
from functools import update_wrapper

from remo.profiles.models import FunctionalArea, UserAvatar, UserProfile
from remo.profiles.tasks import check_celery

# Unregister User from Administration to attach UserProfileInline
admin.site.unregister(User)


def export_mentorship_csv(modeladmin, request, queryset):
    """Export mentorship csv from admin site."""
    today = now().strftime('%Y-%m-%d-%H:%M')
    filename = 'mentorship-%s.csv' % today
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = ('attachment; filename="%s"' %
                                       filename)
    mentorship = []

    for user in queryset.filter(groups__name='Mentor'):
        column = [user.get_full_name().encode('utf-8')]
        column += [u.user.get_full_name().encode('utf-8')
                   for u in user.mentees.all()]
        mentorship.append(column)
    writer = csv.writer(response)
    writer.writerows(izip_longest(*mentorship, fillvalue=None))
    return response


class UserProfileInline(admin.StackedInline):
    """ReportLink Inline."""
    model = UserProfile
    fk_name = 'user'


class UserAdmin(UserAdmin):
    """User Admin."""
    inlines = [UserProfileInline]
    actions = [export_mentorship_csv]

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


class UserAvatarAdmin(admin.ModelAdmin):
    """UserAvatar Admin."""
    list_display = ('display_name', 'avatar_url', 'last_update')

    def display_name(self, obj):
        return obj.user.userprofile.display_name


class FunctionalAreaAdmin(admin.ModelAdmin):
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

admin.site.register(User, UserAdmin)
admin.site.register(FunctionalArea, FunctionalAreaAdmin)
admin.site.register(UserAvatar, UserAvatarAdmin)
