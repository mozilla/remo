from django.forms.models import inlineformset_factory, model_to_dict

from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.events.forms import (BaseEventMetricsFormset, EventForm,
                               EventMetricsForm, PostEventForm)
from remo.events.models import Event
from remo.events.tests import (EventFactory, EventMetricFactory,
                               EventMetricOutcomeFactory)
from remo.profiles.tests import FunctionalAreaFactory, UserFactory
from remo.reports import ACTIVITY_POST_EVENT_METRICS
from remo.reports.models import Activity, NGReport


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
        functional_area = [FunctionalAreaFactory.create()]
        event = EventFactory.create(owner=owner, categories=functional_area)

        data = model_to_dict(event)
        data['categories'] = functional_area[0].id
        data.update(start_form)
        data.update(end_form)

        form = EventForm(data=data, editable_owner=False, instance=event)
        ok_(form.is_valid())
        result = form.save()
        ok_(functional_area[0] in result.categories.all())


class EventMetricsFormsetTest(RemoTestCase):

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
                ok_(metric not in metric_field.queryset.all())

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
        FunctionalAreaFactory.create_batch(3)

        data = {
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


class PostEventFormTest(RemoTestCase):
    def test_passive_report_save(self):
        """Test that a passive report is created on form save()"""
        start_form = {
            'start_form_0_month': 1,
            'start_form_0_day': 25,
            'start_form_0_year': 2013,
            'start_form_1_hour': 4,
            'start_form_1_minute': 1}
        end_form = {
            'end_form_0_month': 1,
            'end_form_0_day': 26,
            'end_form_0_year': 2013,
            'end_form_1_hour': 4,
            'end_form_1_minute': 1}

        owner = UserFactory.create(groups=['Rep', 'Mentor'])
        areas = [FunctionalAreaFactory.create()]
        event = EventFactory.create(owner=owner, categories=areas)

        data = model_to_dict(event)
        data['categories'] = areas[0].id
        data.update(start_form)
        data.update(end_form)

        form = PostEventForm(data=data, editable_owner=False, instance=event)

        activity = Activity.objects.get(name=ACTIVITY_POST_EVENT_METRICS)
        reports = NGReport.objects.filter(user=owner, activity=activity)
        ok_(not reports.exists())
        ok_(form.is_valid())
        form.save()

        reports = NGReport.objects.filter(user=owner, activity=activity)
        ok_(reports.count(), 1)
