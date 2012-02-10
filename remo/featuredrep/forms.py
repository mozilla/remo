from django import forms
# You should be importing from happyforms instead, since this version of Django doesn't trim
# whitespace
# https://github.com/mozilla/happyforms

from models import FeaturedRep
# Two line breaks to start a class. You should be running check.py on all your files to
# conform to pep8 standards
# https://github.com/jbalogh/check
class FeaturedRepForm(forms.ModelForm):
    class Meta:
        model = FeaturedRep
        fields = ('user', 'text')
