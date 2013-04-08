import happyforms

from models import FeaturedRep


class FeaturedRepForm(happyforms.ModelForm):
    """Form to create a new FeaturedRep object."""

    class Meta:
        model = FeaturedRep
        fields = ('user', 'text')
