from django.shortcuts import get_object_or_404

import django_filters
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response

from remo.profiles.api.serializers import (UserProfileDetailedSerializer,
                                           UserSerializer)
from remo.profiles.models import UserProfile


class UserProfileFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(name='user__first_name')
    last_name = django_filters.CharFilter(name='user__last_name')
    groups = django_filters.CharFilter(name='user__groups__name')
    functional_areas = django_filters.CharFilter(name='functional_areas__name')
    mentor = django_filters.CharFilter(name='mentor__userprofile')

    class Meta:
        model = UserProfile
        fields = {
            'user__first_name': ['exact', 'icontains'],
            'user__last_name': ['exact', 'icontains'],
            'user__groups__name': ['exact', 'icontains'],
            'display_name': ['exact', 'icontains'],
            'date_joined_program': ['exact', 'lt', 'lte', 'gt', 'gte'],
            'date_left_program': ['exact', 'lt', 'lte', 'gt', 'gte'],
            'city': ['exact', 'icontains'],
            'region': ['exact', 'icontains'],
            'country': ['exact', 'icontains'],
            'twitter_account': ['exact', 'icontains'],
            'jabber_id': ['exact', 'icontains'],
            'irc_name': ['exact', 'icontains'],
            'wiki_profile_url': ['exact', 'icontains'],
            'irc_channels': ['exact', 'icontains'],
            'linkedin_url': ['exact', 'icontains'],
            'facebook_url': ['exact', 'icontains'],
            'diaspora_url': ['exact', 'icontains'],
            'functional_areas__name': ['exact', 'icontains'],
            'bio': ['exact', 'icontains'],
            'mentor__userprofile': ['exact'],
            'mozillians_profile_url': ['exact', 'icontains'],
        }


class UserProfileViewSet(ReadOnlyModelViewSet):
    """Returns a list of Reps profiles."""
    serializer_class = UserSerializer
    model = UserProfile
    queryset = UserProfile.objects.all()

    def get_queryset(self):
        queryset = self.queryset.filter(
            user__groups__name='Rep', registration_complete=True)
        return queryset

    def retrieve(self, request, pk):
        userprofile = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = UserProfileDetailedSerializer(
            userprofile, context={'request': request})
        return Response(serializer.data)
