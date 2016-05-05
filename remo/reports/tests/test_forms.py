from datetime import date
from django.forms.models import model_to_dict

from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.profiles.tests import FunctionalAreaFactory, UserFactory
from remo.reports import ACTIVITY_CAMPAIGN
from remo.reports.forms import NGReportForm
from remo.reports.models import NGReport
from remo.reports.tests import (ActivityFactory, CampaignFactory,
                                NGReportFactory)


class NGReportFormTests(RemoTestCase):
    def test_base(self):
        user = UserFactory.create()
        activity = ActivityFactory.create()
        campaign = CampaignFactory.create()
        functional_area = FunctionalAreaFactory.create()
        data = {
            'report_date': '25 March 2012',
            'activity': activity.id,
            'campaign': campaign.id,
            'longitude': 44.33,
            'latitude': 55.66,
            'location': 'world',
            'link': 'https://example.com',
            'link_description': 'Test link.',
            'activity_description': 'Test activity',
            'functional_areas': functional_area.id,
        }
        form = NGReportForm(data, instance=NGReport(user=user))
        ok_(form.is_valid())
        db_obj = form.save()
        eq_(db_obj.report_date, date(2012, 03, 25))
        eq_(db_obj.activity, activity)
        eq_(db_obj.longitude, 44.33)
        eq_(db_obj.latitude, 55.66)
        eq_(db_obj.location, 'world')
        eq_(db_obj.link, 'https://example.com')
        eq_(db_obj.link_description, 'Test link.')
        eq_(db_obj.activity_description, 'Test activity'),
        eq_(db_obj.functional_areas.all().count(), 1)
        eq_(db_obj.functional_areas.all()[0], functional_area)
        eq_(db_obj.mentor, user.userprofile.mentor)

    def test_report_date_in_future(self):
        data = {
            'report_date': '25 March 3000',
        }
        form = NGReportForm(data)
        ok_(not form.is_valid())
        ok_('report_date' in form.errors)
        ok_(form.errors['report_date'],
            'Report date cannot be in the future.')

    def test_campain_activity_without_campaign(self):
        activity = ActivityFactory.create(name=ACTIVITY_CAMPAIGN)
        data = {
            'activity': activity.id
        }
        form = NGReportForm(data)
        ok_(not form.is_valid())
        ok_('campaign' in form.errors)
        ok_(form.errors['campaign'],
            'Please select an option from the list.')


class InactiveCategoriesTest(RemoTestCase):

    def test_edit_event(self):
        """Edit NGReport with inactive categories."""
        activity = ActivityFactory.create()
        campaign = CampaignFactory.create()
        active_area = FunctionalAreaFactory.create()
        inactive_areas = FunctionalAreaFactory.create_batch(2, active=False)
        report = NGReportFactory.create(activity=activity, campaign=campaign,
                                        functional_areas=inactive_areas)

        data = model_to_dict(report)
        data['functional_areas'] = active_area.id
        form = NGReportForm(data, instance=report)
        ok_(form.is_valid())
        result = form.save()
        ok_(active_area in result.functional_areas.all())
        eq_(result.functional_areas.all().count(), 1)
