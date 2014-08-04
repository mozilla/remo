import factory

from remo.featuredrep.models import FeaturedRep
from remo.profiles.tests import UserFactory


class FeaturedRepFactory(factory.django.DjangoModelFactory):
    """Factory for FeaturedRep model."""
    FACTORY_FOR = FeaturedRep

    created_by = factory.SubFactory(UserFactory)

    @factory.post_generation
    def users(self, create, extracted, **kwargs):
        """Add users as Featured Reps after factory creation."""
        if not create:
            return
        if extracted:
            for user in extracted:
                self.users.add(user)
        else:
            # add two users as FeaturedRep
            for i in range(2):
                area = UserFactory.create()
                self.users.add(area)
