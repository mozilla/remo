from django.test import RequestFactory

from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.events.tests import EventFactory
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
