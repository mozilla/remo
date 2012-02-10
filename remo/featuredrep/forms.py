from happyforms import forms

from models import FeaturedRep


class FeaturedRepForm(forms.ModelForm):
    class Meta:
        model = FeaturedRep
        fields = ('user', 'text')
