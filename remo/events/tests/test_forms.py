from django.forms.models import inlineformset_factory, model_to_dict

from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.events.forms import (BaseEventMetricsFormset, EventForm,
                               EventMetricsForm)
from remo.events.models import Event
from remo.events.tests import (EventFactory, EventGoalFactory,
                               EventMetricFactory,
                               EventMetricOutcomeFactory)
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


class EventMetricsFormset(RemoTestCase):
    def test_inactive_metrics_new(self):
        """Test active/inactive queryset in new event."""
        active_metrics = EventMetricFactory.create_batch(3)
        inactive_metrics = EventMetricFactory.create_batch(3, active=False)

        formset = inlineformset_factory(
            Event, Event.metrics.through,
            form=EventMetricsForm,
            formset=BaseEventMetricsFormset,
            extra=2)

        forms = formset(instance=Event())

        for form in forms:
            metric_field = form.fields['metric']
            for metric in active_metrics:
                ok_(metric in metric_field.queryset.all())

            for metric in inactive_metrics:
                ok_(not metric in metric_field.queryset.all())

    def test_inactive_metrics_edit(self):
        """Test active/inactive queryset in event edit."""
        inactive_metrics = EventMetricFactory.create_batch(3, active=False)
        active_metrics = EventMetricFactory.create_batch(3)
        metrics = active_metrics + inactive_metrics
        event = EventFactory.create()

        for metric in metrics:
            EventMetricOutcomeFactory.create(event=event, metric=metric)

        formset = inlineformset_factory(
            Event, Event.metrics.through,
            form=EventMetricsForm,
            formset=BaseEventMetricsFormset,
            extra=0)

        forms = formset(instance=event)

        for form in forms:
            metric_field = form.fields['metric']
            for metric in metrics:
                ok_(metric in metric_field.queryset.all())

    def test_invalid_formset(self):
        """Test unique metrics validation."""
        metrics = EventMetricFactory.create_batch(2)
        categories = FunctionalAreaFactory.create_batch(3)
        goals = EventGoalFactory.create_batch(3)

        data = {
            'name': u'Test edit event',
            'description': u'This is a description',
            'external_link': '',
            'categories': [x.id for x in categories],
            'goals': [x.id for x in goals],
            'venue': u'Hackerspace.GR',
            'lat': 38.01697,
            'lon': 23.7314,
            'city': u'Athens',
            'region': u'Attica',
            'country': u'Greece',
            'start_form_0_month': 01,
            'start_form_0_day': 25,
            'start_form_0_year': 2014,
            'start_form_1_hour': 04,
            'start_form_1_minute': 01,
            'end_form_0_month': 01,
            'end_form_0_day': 03,
            'end_form_0_year': 2018,
            'end_form_1_hour': 03,
            'end_form_1_minute': 00,
            'timezone': u'Europe/Athens',
            'mozilla_event': u'on',
            'estimated_attendance': u'10',
            'extra_content': u'This is extra content',
            'planning_pad_url': u'',
            'hashtag': u'#testevent',
            'swag_bug_form': u'',
            'budget_bug_form': u'',
            'eventmetricoutcome_set-0-id': '',
            'eventmetricoutcome_set-0-metric': metrics[0].id,
            'eventmetricoutcome_set-0-expected_outcome': 100,
            'eventmetricoutcome_set-1-id': '',
            'eventmetricoutcome_set-1-metric': metrics[0].id,
            'eventmetricoutcome_set-1-expected_outcome': 10,
            'eventmetricoutcome_set-2-id': '',
            'eventmetricoutcome_set-2-metric': metrics[1].id,
            'eventmetricoutcome_set-2-expected_outcome': 10,
            'eventmetricoutcome_set-TOTAL_FORMS': 2,
            'eventmetricoutcome_set-INITIAL_FORMS': 0}

        formset = inlineformset_factory(
            Event, Event.metrics.through,
            form=EventMetricsForm,
            formset=BaseEventMetricsFormset,
            extra=2)

        forms = formset(instance=Event(), data=data)
        error_msg = 'This metric has already been selected.'
        ok_(not forms.is_valid())
        eq_(forms.errors[1]['metric'], error_msg)
