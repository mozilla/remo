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
    list_display = ('__unicode__', 'registered_reps')

    def registered_reps(self, obj):
        return UserProfile.objects.filter(functional_areas=obj).count()


admin.site.register(User, UserAdmin)
admin.site.register(FunctionalArea, FunctionalAreaAdmin)
admin.site.register(UserAvatar, UserAvatarAdmin)
