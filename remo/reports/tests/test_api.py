from datetime import date, datetime
from mock import patch

from django.test import RequestFactory

from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.events.tests import EventFactory
from remo.reports.api.views import ActivitiesKPIView
from remo.reports.api.serializers import (ActivitiesDetailedSerializer,
                                          ActivitiesSerializer)
from remo.reports.tests import (ActivityFactory, CampaignFactory,
                                NGReportFactory)
from remo.profiles.tests import FunctionalAreaFactory, UserFactory


class TestActivitySerializer(RemoTestCase):

    def test_base(self):
        activity = ActivityFactory.create()
        report = NGReportFactory.create(activity=activity)
        url = '/api/beta/activities/%s' % report.id
        request = RequestFactory().get(url)
        serializer = ActivitiesSerializer(report,
                                          context={'request': request})
        eq_(serializer.data['activity'], activity.name)
        ok_(serializer.data['_url'])


class TestActivityDetailedSerializer(RemoTestCase):

    def test_base(self):
        mentor = UserFactory.create()
        user = UserFactory.create(userprofile__mentor=mentor)
        event = EventFactory.create()
        functional_areas = [FunctionalAreaFactory.create()]
        campaign = CampaignFactory.create()
        activity = ActivityFactory.create()
        report = NGReportFactory.create(
            functional_areas=functional_areas, mentor=mentor,
            campaign=campaign, user=user, event=event, activity=activity)
        url = '/api/beta/activities/%s' % report.id
        request = RequestFactory().get(url)
        data = ActivitiesDetailedSerializer(report,
                                            context={'request': request}).data
        eq_(data['user']['first_name'], user.first_name)
        eq_(data['user']['last_name'], user.last_name)
        eq_(data['user']['display_name'], user.userprofile.display_name)
        ok_(data['user']['_url'])
        eq_(data['activity'], activity.name)
        eq_(data['initiative'], campaign.name)
        eq_(data['functional_areas'][0]['name'], functional_areas[0].name)
        eq_(data['activity_description'], report.activity_description)
        eq_(data['location'], report.location)
        eq_(data['latitude'], float(report.latitude))
        eq_(data['longitude'], float(report.longitude))
        eq_(data['report_date'], report.report_date.strftime('%Y-%m-%d'))
        eq_(data['link'], report.link)
        eq_(data['link_description'], report.link_description)
        eq_(data['mentor']['first_name'], mentor.first_name)
        eq_(data['mentor']['last_name'], mentor.last_name)
        eq_(data['mentor']['display_name'], mentor.userprofile.display_name)
        ok_(data['mentor']['_url'])
        eq_(data['passive_report'], report.is_passive)
        eq_(data['event']['name'], event.name)
        ok_(data['event']['_url'])

    def test_get_remo_url(self):
        report = NGReportFactory.create()
        url = '/api/beta/activities/%s' % report.id
        request = RequestFactory().get(url)
        data = ActivitiesDetailedSerializer(
            report, context={'request': request}).data
        ok_(report.get_absolute_url() in data['remo_url'])


class TestActivitiesKPIView(RemoTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.url = '/api/kpi/activities'

    def test_total(self):
        NGReportFactory.create()
        request = self.factory.get(self.url)
        request.query_params = dict()
        response = ActivitiesKPIView().get(request)
        eq_(response.data['total'], 1)

    @patch('remo.reports.api.views.now')
    def test_quarter(self, mock_now):
        mock_now.return_value = datetime(2015, 3, 1)

        # Previous quarter
        report_date = date(2014, 12, 5)
        NGReportFactory.create_batch(2, report_date=report_date)

        # This quarter
        report_date = date(2015, 1, 5)
        NGReportFactory.create(report_date=report_date)

        # Next quarter
        report_date = date(2015, 5, 3)
        NGReportFactory.create(report_date=report_date)

        request = self.factory.get(self.url)
        request.query_params = dict()

        response = ActivitiesKPIView().get(request)
        eq_(response.data['quarter_total'], 1)
        eq_(response.data['quarter_growth_percentage'], (3-2)*100/2.0)

    @patch('remo.reports.api.views.now')
    def test_current_week(self, mock_now):
        mock_now.return_value = datetime(2015, 3, 1)

        # Current week
        report_date = date(2015, 2, 25)
        NGReportFactory.create(report_date=report_date)

        # Previous week
        report_date = date(2015, 2, 18)
        NGReportFactory.create_batch(2, report_date=report_date)

        # Next week
        report_date = date(2015, 3, 4)
        NGReportFactory.create(report_date=report_date)

        request = self.factory.get(self.url)
        request.query_params = dict()

        response = ActivitiesKPIView().get(request)
        eq_(response.data['week_total'], 1)
        eq_(response.data['week_growth_percentage'], (1-2)*100/2.0)

    @patch('remo.reports.api.views.now')
    def test_weeks(self, mock_now):
        mock_now.return_value = datetime(2015, 3, 1)

        # Current week
        report_date = date(2015, 2, 26)
        NGReportFactory.create_batch(3, report_date=report_date)

        # Week-1
        report_date = date(2015, 2, 18)
        NGReportFactory.create_batch(2, report_date=report_date)

        # Week-2
        report_date = date(2015, 2, 11)
        NGReportFactory.create_batch(4, report_date=report_date)

        # Week-3
        report_date = date(2015, 2, 4)
        NGReportFactory.create(report_date=report_date)

        # Next week
        report_date = date(2015, 3, 4)
        NGReportFactory.create(report_date=report_date)

        request = self.factory.get(self.url)
        request.query_params = {'weeks': 4}

        response = ActivitiesKPIView().get(request)
        eq_(response.data['week_total'], 3)
        eq_(response.data['week_growth_percentage'], (3-2)*100/2.0)
        total_per_week = [
            {'week': 1, 'activities': 1},
            {'week': 2, 'activities': 4},
            {'week': 3, 'activities': 2},
            {'week': 4, 'activities': 3}
        ]

        for entry in response.data['total_per_week']:
            ok_(entry in total_per_week)

        eq_(len(response.data['total_per_week']), 4)
