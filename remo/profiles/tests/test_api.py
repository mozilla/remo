from datetime import date, datetime

from django.contrib.auth.models import Group
from django.test import RequestFactory

from mock import patch
from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.profiles.api.serializers import (FunctionalAreaSerializer,
                                           GroupSerializer,
                                           UserProfileDetailedSerializer,
                                           UserSerializer)
from remo.profiles.api.views import PeopleKPIView
from remo.profiles.tests import FunctionalAreaFactory, UserFactory


# Test serialisers
class TestFunctionalAreaSerializer(RemoTestCase):

    def test_base(self):
        functional_area = FunctionalAreaFactory.create()
        serializer = FunctionalAreaSerializer(functional_area)
        eq_(serializer.data, {'name': functional_area.name})


class TestGroupSerializer(RemoTestCase):

    def test_base(self):
        group = Group.objects.get(name='Mozillians')
        serializer = GroupSerializer(group)
        eq_(serializer.data, {'name': group.name})


class TestUserSerializer(RemoTestCase):

    def test_base(self):
        user = UserFactory.create()
        url = '/api/beta/users/%s' % user.id
        request = RequestFactory().get(url)
        serializer = UserSerializer(user, context={'request': request})
        eq_(serializer.data['first_name'], user.first_name)
        eq_(serializer.data['last_name'], user.last_name)
        eq_(serializer.data['display_name'], user.userprofile.display_name)
        ok_(serializer.data['_url'])


class TestUserProfileDetailedSerializer(RemoTestCase):

    def test_base(self):
        mentor = UserFactory.create()
        functional_areas = FunctionalAreaFactory.create_batch(2)
        user = UserFactory.create(
            userprofile__mentor=mentor, groups=['Rep'],
            userprofile__functional_areas=functional_areas)
        url = '/api/beta/users/%s' % user.id
        request = RequestFactory().get(url)
        profile = user.userprofile
        data = UserProfileDetailedSerializer(user.userprofile,
                                             context={'request': request}).data
        eq_(data['first_name'], user.first_name)
        eq_(data['last_name'], user.last_name)
        eq_(data['display_name'], profile.display_name)
        eq_(data['date_joined_program'],
            profile.date_joined_program.strftime('%Y-%m-%d'))
        eq_(data['date_left_program'], profile.date_left_program)
        eq_(data['city'], profile.city)
        eq_(data['region'], profile.region)
        eq_(data['country'], profile.country)
        eq_(data['twitter_account'], profile.twitter_account)
        eq_(data['jabber_id'], profile.jabber_id)
        eq_(data['irc_name'], profile.irc_name)
        eq_(data['wiki_profile_url'], profile.wiki_profile_url)
        eq_(data['irc_channels'], profile.irc_channels)
        eq_(data['linkedin_url'], profile.linkedin_url)
        eq_(data['facebook_url'], profile.facebook_url)
        eq_(data['diaspora_url'], profile.diaspora_url)
        eq_(data['bio'], profile.bio)
        eq_(data['mozillians_profile_url'], profile.mozillians_profile_url)
        eq_(data['timezone'], profile.timezone)
        eq_(data['groups'][0]['name'], 'Rep')
        eq_(data['mentor']['first_name'], mentor.first_name)
        eq_(data['mentor']['last_name'], mentor.last_name)
        eq_(data['mentor']['display_name'], mentor.userprofile.display_name)
        ok_(data['mentor']['_url'])
        eq_(data['functional_areas'][0]['name'], functional_areas[0].name)
        eq_(data['functional_areas'][1]['name'], functional_areas[1].name)

    def test_get_remo_url(self):
        mentor = UserFactory.create()
        functional_areas = FunctionalAreaFactory.create_batch(2)
        user = UserFactory.create(
            userprofile__mentor=mentor, groups=['Rep'],
            userprofile__functional_areas=functional_areas)
        url = '/api/beta/users/%s' % user.id
        request = RequestFactory().get(url)
        data = UserProfileDetailedSerializer(user.userprofile,
                                             context={'request': request}).data
        ok_(user.userprofile.get_absolute_url() in data['remo_url'])


class TestPeopleKPIView(RemoTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.url = '/api/kpi/people'

    def test_total(self):
        UserFactory.create(groups=['Rep'])
        request = self.factory.get(self.url)
        request.query_params = dict()
        response = PeopleKPIView().get(request)
        eq_(response.data['total'], 1)

    @patch('remo.profiles.api.views.get_quarter')
    def test_quarter(self, mocked_quarter):
        mocked_quarter.return_value = (1, date(2015, 3, 1))

        # Previous quarter
        start = datetime(2014, 12, 5)
        UserFactory.create(groups=['Rep'],
                           userprofile__date_joined_program=start)

        # This quarter
        start = datetime(2015, 1, 5)
        UserFactory.create(groups=['Rep'],
                           userprofile__date_joined_program=start)

        # Next quarter
        start = datetime(2015, 5, 3)
        UserFactory.create(groups=['Rep'],
                           userprofile__date_joined_program=start)

        request = self.factory.get(self.url)
        request.query_params = dict()

        response = PeopleKPIView().get(request)
        eq_(response.data['quarter_total'], 1)
        eq_(response.data['quarter_growth_percentage'], 100)

    @patch('remo.profiles.api.views.now')
    @patch('remo.base.utils.timezone.now')
    def test_current_week(self, mock_api_now, mock_utils_now):
        now_return_value = datetime(2015, 3, 1)
        mock_api_now.return_value = now_return_value
        mock_utils_now.return_value = now_return_value

        # Current week
        start = datetime(2015, 2, 22)
        UserFactory.create(groups=['Rep'],
                           userprofile__date_joined_program=start)

        # Previous week
        start = datetime(2015, 2, 18)
        UserFactory.create(groups=['Rep'],
                           userprofile__date_joined_program=start)

        # Next week
        start = datetime(2015, 3, 4)
        UserFactory.create(groups=['Rep'],
                           userprofile__date_joined_program=start)

        request = self.factory.get(self.url)
        request.query_params = dict()

        response = PeopleKPIView().get(request)
        eq_(response.data['week_total'], 1)
        eq_(response.data['week_growth_percentage'], (1-2)*100/2.0)
