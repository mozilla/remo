from happyforms import forms

from models import FeaturedRep


class FeaturedRepForm(forms.ModelForm):
    """ Form to create a new FeaturedRep object """
    class Meta:
        model = FeaturedRep
        fields = ('user', 'text')
