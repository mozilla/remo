from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from remo.profiles.models import FunctionalArea, UserAvatar, UserProfile

# Unregister User from Administration to attach UserProfileInline
admin.site.unregister(User)


class UserProfileInline(admin.StackedInline):
    """ReportLink Inline."""
    model = UserProfile
    fk_name = 'user'


class UserAdmin(UserAdmin):
    """User Admin."""
    inlines = [UserProfileInline]


class UserAvatarAdmin(admin.ModelAdmin):
    """UserAvatar Admin."""
    list_display = ('display_name', 'avatar_url', 'last_update')

    def display_name(self, obj):
        return obj.user.userprofile.display_name


class FunctionalAreaAdmin(admin.ModelAdmin):
    """FunctionalArea Admin."""
    list_display = ('name', 'registered_reps', 'registered_mozillians')

    def registered_reps(self, obj):
        return obj.users_matching.count()

    def registered_mozillians(self, obj):
        return obj.users_tracking.count()


admin.site.register(User, UserAdmin)
admin.site.register(FunctionalArea, FunctionalAreaAdmin)
admin.site.register(UserAvatar, UserAvatarAdmin)
