from django.shortcuts import get_object_or_404

from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response

from remo.profiles.api.serializers import (UserProfileDetailedSerializer,
                                           UserSerializer)
from remo.profiles.models import UserProfile


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
