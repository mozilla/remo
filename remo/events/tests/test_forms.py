from django.forms.models import model_to_dict

from nose.tools import ok_

from remo.base.tests import RemoTestCase
from remo.events.forms import EventForm
from remo.events.tests import EventFactory
from remo.profiles.tests import FunctionalAreaFactory, UserFactory


class InactiveCategoriesTest(RemoTestCase):
    def test_edit_event(self):
        """Edit event with inactive categories."""
        start_form = {
            'start_form_0_month': 1,
            'start_form_0_day': 25,
            'start_form_0_year': 2014,
            'start_form_1_hour': 4,
            'start_form_1_minute': 1}
        end_form = {
            'end_form_0_month': 1,
            'end_form_0_day': 25,
            'end_form_0_year': 2015,
            'end_form_1_hour': 4,
            'end_form_1_minute': 1}

        owner = UserFactory.create(groups=['Mentor'])
        active_areas = FunctionalAreaFactory.create_batch(2)
        inactive_areas = FunctionalAreaFactory.create_batch(2, active=False)
        event = EventFactory.create(owner=owner, categories=inactive_areas)

        data = model_to_dict(event)
        data['categories'] = [x.id for x in active_areas + inactive_areas]
        data.update(start_form)
        data.update(end_form)

        form = EventForm(data=data, editable_owner=False, instance=event)
        ok_(form.is_valid())
        result = form.save()
        for area in active_areas + inactive_areas:
            ok_(area in result.categories.all())
