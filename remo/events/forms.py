from happyforms import forms
from product_details import product_details

from models import Event


class EventForm(forms.ModelForm):
    """Form of an event."""
    country = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        """Initialize form.

        Dynamically set choices for country field.
        """
        super(EventForm, self).__init__(*args, **kwargs)
        countries = product_details.get_regions('en').values()
        countries.sort()
        country_choices = ([(None, "Country")] +
                           [(country, country) for country in countries])
        self.fields['country'].choices = country_choices

    def clean(self):
        """Clean form.

        Make sure that no lon/lat values are stored for virtual
        events.

        """
        cleaned_data = super(EventForm, self).clean()
        if (cleaned_data['virtual_event'] == True):
            cleaned_data['lat'] = None
            cleaned_data['lon'] = None

        return cleaned_data

    class Meta:
        model = Event
        fields = ['name', 'start', 'end', 'venue', 'region',
                  'country', 'lat', 'lon', 'external_link',
                  'estimated_attendance', 'description', 'extra_content',
                  'hashtag', 'mozilla_event', 'virtual_event']
        widgets = {'lat': forms.HiddenInput(attrs={'id': 'lat'}),
                   'lon': forms.HiddenInput(attrs={'id': 'lon'})}
