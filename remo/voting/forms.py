import happyforms
from django import forms

from django.db.models import F

from models import RangePollChoice, RadioPollChoice


class RangePollChoiceForm(happyforms.Form):
    """Range voting vote form."""
    def __init__(self, choices, *args, **kwargs):
        """Initialize form

        Dynamically set fields for the participants in a range voting.
        """
        super(RangePollChoiceForm, self).__init__(*args, **kwargs)
        nominees = [(i, '%d' % i) for i in range(0, choices.count()+1)]
        for choice in choices:
            self.fields['range_poll__%s' % str(choice.id)] = (
                forms.ChoiceField(widget=forms.Select(),
                                  choices=nominees,
                                  label=choice.nominee.get_full_name()))

    def save(self, *args, **kwargs):
        for nominee_id, votes in self.cleaned_data.items():
            nominee_id = nominee_id.split('__')[1]
            (RangePollChoice.objects
             .filter(pk=nominee_id).update(votes=F('votes')+int(votes)))


class RadioPollChoiceForm(happyforms.Form):
    """Radio voting vote form."""
    def __init__(self, radio_poll, *args, **kwargs):
        """Initialize form

        Dynamically set field for the answers in a radio voting.
        """
        super(RadioPollChoiceForm, self).__init__(*args, **kwargs)
        choices = (((None, '----'),) +
                   tuple(radio_poll.answers.values_list('id', 'answer')))
        self.fields['radio_poll__%s' % str(radio_poll.id)] = (
            forms.ChoiceField(widget=forms.Select(),
                              choices=choices,
                              label=radio_poll.question))

    def save(self, *args, **kwargs):
        answer_id = self.cleaned_data.values()[0]
        if answer_id != 'None':
            (RadioPollChoice.objects
             .filter(pk=answer_id).update(votes=F('votes')+1))
