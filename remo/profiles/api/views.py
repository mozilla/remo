from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response

from remo.profiles.api.serializers import (UserProfileDetailedSerializer,
                                           UserSerializer)


class UserProfileViewSet(ReadOnlyModelViewSet):
    """Returns a list of Reps profiles."""
    serializer_class = UserSerializer
    model = User
    queryset = User.objects.all()

    def get_queryset(self):
        queryset = self.queryset.filter(
            groups__name='Rep', userprofile__registration_complete=True)
        return queryset

    def retrieve(self, request, pk):
        user = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = UserProfileDetailedSerializer(
            user.userprofile, context={'request': request})
        return Response(serializer.data)
