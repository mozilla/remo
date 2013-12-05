import datetime

from django.contrib.auth.models import Group, Permission
from django.core.urlresolvers import reverse
from django.test.client import Client
from funfactory.helpers import urlparams
from nose.tools import eq_, nottest
from test_utils import TestCase

import mock
from waffle import Flag

from remo.base.utils import go_back_n_months
from remo.profiles.tests import UserFactory
from remo.reports.models import NGReport, ReportComment
from remo.reports.tests import (ActivityFactory, CampaignFactory,
                                NGReportFactory, ReportCommentFactory,
                                ReportFactory)
from remo.reports.views import LIST_REPORTS_VALID_SHORTS


class ViewsTest(TestCase):
    """Tests related to Reports Views."""

    def setUp(self):
        """Setup tests."""
        self.admin = UserFactory.create(username='admin', groups=['Admin'])
        self.counselor = UserFactory.create(username='counselor')
        self.mentor = UserFactory.create(username='mentor', groups=['Mentor'])
        self.user = UserFactory.create(username='rep', groups=['Rep'],
                                       userprofile__mentor=self.mentor)
        self.up = self.user.userprofile

        self.data = {'empty': False,
                     'recruits': '10',
                     'recruits_comments': 'This is recruit comments.',
                     'past_items': 'This is past items.',
                     'next_items': 'This is next items.',
                     'flags': 'This is flags.',
                     'delete_report': False,
                     'reportevent_set-TOTAL_FORMS': '1',
                     'reportevent_set-INITIAL_FORMS': '0',
                     'reportevent_set-MAX_NUM_FORMS': '',
                     'reportevent_set-0-id': '',
                     'reportevent_set-0-name': 'Event name',
                     'reportevent_set-0-description': 'Event description',
                     'reportevent_set-0-link': 'http://example.com/evtlnk',
                     'reportevent_set-0-participation_type': '1',
                     'reportevent_set-0-DELETE': False,
                     'reportlink_set-TOTAL_FORMS': '1',
                     'reportlink_set-INITIAL_FORMS': '0',
                     'reportlink_set-MAX_NUM_FORMS': '',
                     'reportlink_set-0-id': '',
                     'reportlink_set-0-link': 'http://example.com/link',
                     'reportlink_set-0-description': 'This is description',
                     'reportlink_set-0-DELETE': False}

    def test_view_reports_list(self):
        """Test view report list page."""
        c = Client()
        response = c.get(reverse('reports_list_reports'))
        self.assertTemplateUsed(response, 'reports_list.html')

        for sort_key in LIST_REPORTS_VALID_SHORTS:
            response = c.get(urlparams(reverse('reports_list_reports'),
                                       sort_key=sort_key))
            self.assertTemplateUsed(response, 'reports_list.html')

        # Test pagination.
        response = c.get(urlparams(reverse('reports_list_reports'), page=1))
        self.assertTemplateUsed(response, 'reports_list.html')

    def test_view_current_report_page(self):
        """Test view report page."""
        # If anonymous, return an error.
        c = Client()
        response = c.get(reverse('reports_view_current_report'), follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'warning')

        # Login.
        c.login(username='rep', password='passwd')

        # If report does not exist, render edit page.
        response = c.get(reverse('reports_view_current_report'), follow=True)
        self.assertTemplateUsed(response, 'edit_report.html')

        # If report exists, render report.
        ReportFactory.create(user=self.user, empty=True, mentor=self.mentor,
                             month=go_back_n_months(datetime.date.today()))
        response = c.get(reverse('reports_view_current_report'), follow=True)
        self.assertTemplateUsed(response, 'view_report.html')

    def test_edit_current_report_page(self):
        """Test view report page."""
        c = Client()
        c.login(username='rep', password='passwd')
        response = c.get(reverse('reports_edit_current_report'), follow=True)
        self.assertTemplateUsed(response, 'edit_report.html')

    def test_view_report_page(self):
        """Test view report page."""
        # check that there is comment
        # check that there is comment form
        ReportFactory.create(user=self.user, empty=True, mentor=self.mentor,
                             month=datetime.date(2012, 1, 1))
        c = Client()
        response = c.get(reverse('reports_view_report',
                                 kwargs={'display_name': self.up.display_name,
                                         'year': '2012',
                                         'month': 'January'}))
        self.assertTemplateUsed(response, 'view_report.html')

    def test_view_nonexistent_report_page(self):
        """Test view nonexistent report page."""
        c = Client()
        response = c.get(reverse('reports_view_report',
                                 kwargs={'display_name': self.up.display_name,
                                         'year': '2011',
                                         'month': 'January'}))
        self.assertTemplateUsed(response, '404.html')

    def test_view_edit_report_page(self):
        """Test view edit report page."""
        # test my edit report
        # test without permission other user's
        # test with permission other user's
        # test with report from the future
        ReportFactory.create(user=self.user, empty=True, mentor=self.mentor,
                             month=datetime.date(2011, 2, 1))

        edit_page_url = reverse('reports_edit_report',
                                kwargs={'display_name': self.up.display_name,
                                        'year': '2011',
                                        'month': 'February'})

        # Try to access edit report page as anonymous.
        c = Client()
        response = c.get(edit_page_url, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'warning')

        # Try to access edit report page as owner.
        c.login(username='rep', password='passwd')
        response = c.get(edit_page_url, follow=True)
        self.assertTemplateUsed(response, 'edit_report.html')

        # Try to access edit report page as admin.
        c.login(username='admin', password='passwd')
        response = c.get(edit_page_url, follow=True)
        self.assertTemplateUsed(response, 'edit_report.html')

        # Try to access edit report page as user's mentor.
        c.login(username='mentor', password='passwd')
        response = c.get(edit_page_url, follow=True)
        self.assertTemplateUsed(response, 'edit_report.html')

        # Try to access edit report page as other user.
        c.login(username='counselor', password='passwd')
        response = c.get(edit_page_url, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

    def test_post_comment_on_report(self):
        """Test post comment on report."""
        # Test with anonymous user.
        c = Client()
        ReportFactory.create(user=self.user, empty=True, mentor=self.mentor,
                             month=datetime.date(2012, 1, 1))
        report_view_url = reverse('reports_view_report',
                                  kwargs={'display_name': self.up.display_name,
                                          'year': '2012',
                                          'month': 'January'})
        response = c.post(report_view_url, {'comment': 'This is comment'},
                          follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

        # Test with logged in user.
        c.login(username='mentor', password='passwd')
        response = c.post(report_view_url, {'comment': 'This is comment'},
                          follow=True)
        self.assertTemplateUsed(response, 'view_report.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')
        self.assertIn('This is comment', response.content)

    @nottest
    def test_edit_report(self):
        pass

    def test_delete_report(self):
        """Test delete report."""
        c = Client()
        ReportFactory.create(user=self.user, empty=True, mentor=self.mentor,
                             month=datetime.date(2012, 2, 1))
        delete_url = reverse('reports_delete_report',
                             kwargs={'display_name': self.up.display_name,
                                     'year': '2012',
                                     'month': 'February'})
        tmp_data = self.data.copy()
        tmp_data['delete_report'] = True

        # Test with anonymous user.
        response = c.post(delete_url, tmp_data, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'warning')

        # Test with logged in user.
        c.login(username='counselor', password='passwd')
        response = c.post(delete_url, tmp_data, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

        # Test with owner.
        c.login(username='rep', password='passwd')
        response = c.post(delete_url, tmp_data, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

        # Test with mentor.
        c.login(username='rep', password='passwd')
        response = c.post(delete_url, tmp_data, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

        # Test with admin.
        c.login(username='admin', password='passwd')
        response = c.post(delete_url, tmp_data, follow=True)
        self.assertTemplateUsed(response, 'profiles_view.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')

    def test_delete_comment(self):
        """Test delete report comment."""
        report = ReportFactory.create(user=self.user, empty=True,
                                      mentor=self.mentor,
                                      month=datetime.date(2012, 2, 1))
        ReportCommentFactory.create(report=report, id=9, user=self.user)
        c = Client()
        delete_url = reverse('reports_delete_report_comment',
                             kwargs={'display_name': self.up.display_name,
                                     'year': '2012',
                                     'month': 'February',
                                     'comment_id': '9'})

        # Test with anonymous user.
        response = c.post(delete_url, {}, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'warning')

        # Test with other user.
        c.login(username='counselor', password='passwd')
        response = c.post(delete_url, {}, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

        # Test with owner.
        c.login(username='rep', password='passwd')
        response = c.post(delete_url, {}, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

        # Test with user's mentor.
        c.login(username='mentor', password='passwd')
        response = c.post(delete_url, {}, follow=True)
        self.assertTemplateUsed(response, 'view_report.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')
        eq_(ReportComment.objects.filter(pk=9).exists(), False)

        # Test with admin.
        ReportCommentFactory.create(report=report, id=10, user=self.user)
        delete_url = reverse('reports_delete_report_comment',
                             kwargs={'display_name': self.up.display_name,
                                     'year': '2012',
                                     'month': 'February',
                                     'comment_id': '10'})
        c.login(username='admin', password='passwd')
        response = c.post(delete_url, {}, follow=True)
        self.assertTemplateUsed(response, 'view_report.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')
        eq_(ReportComment.objects.filter(pk=10).exists(), False)


# New generation reports tests
class EditNGReportTests(TestCase):
    """Tests related to New Generation Reports edit View."""

    def setUp(self):
        """Setup tests."""
        # Create waffle flag
        Flag.objects.create(name='reports_ng_report', everyone=True)
        # Give permissions to admin group
        group = Group.objects.get(name='Admin')
        permissions = Permission.objects.filter(codename__icontains='ngreport')
        for perm in permissions:
            group.permissions.add(perm)
        self.mentor = UserFactory.create(username='mentor', groups=['Mentor'])
        self.user = UserFactory.create(username='rep', groups=['Rep'],
                                       userprofile__mentor=self.mentor)

    @mock.patch('remo.base.decorators.messages')
    def test_get_as_anonymous(self, fake_messages):
        """Get edit page as anonymous user."""

        year, month, day = datetime.datetime.now().strftime('%d %B %Y').split()
        edit_report_url = (
            reverse('reports_ng_edit_report',
                    kwargs={'display_name': self.user.userprofile.display_name,
                            'year': year,
                            'month': month,
                            'day': day,
                            'id': '1'}))
        c = Client()
        response = c.get(edit_report_url, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        fake_messages.warning.assert_called_once_with(
            mock.ANY, 'Please login.')

    def test_get_non_existing_report_rep(self):
        """Get edit page as a user who belongs to Rep group,

        for a report that does not exist."""

        year, month, day = datetime.datetime.now().strftime('%d %B %Y').split()
        edit_report_url = (
            reverse('reports_ng_edit_report',
                    kwargs={'display_name': self.user.userprofile.display_name,
                            'year': year,
                            'month': month,
                            'day': day,
                            'id': '1'}))
        c = Client()
        c.login(username='rep', password='passwd')
        response = c.get(edit_report_url, follow=True)
        self.assertTemplateUsed(response, '404.html')

    def test_get_edit_page_rep(self):
        """Get edit page as a user who belongs to Rep group."""

        year, month, day = datetime.datetime.now().strftime('%d %B %Y').split()
        edit_report_url = (
            reverse('reports_ng_edit_report',
                    kwargs={'display_name': self.user.userprofile.display_name,
                            'year': year,
                            'month': month,
                            'day': day,
                            'id': '1'}))
        # Force a report with the same pk as the edit url
        NGReportFactory.create(user=self.user, pk=1)
        c = Client()
        c.login(username='rep', password='passwd')
        response = c.get(edit_report_url, follow=True)
        self.assertTemplateUsed(response, 'edit_ng_report.html')

    @mock.patch('remo.base.decorators.messages')
    def test_get_edit_page_non_rep(self, fake_messages):
        """Get edit page as a user who does not belong to Rep group."""

        year, month, day = datetime.datetime.now().strftime('%d %B %Y').split()
        edit_report_url = (
            reverse('reports_ng_edit_report',
                    kwargs={'display_name': self.user.userprofile.display_name,
                            'year': year,
                            'month': month,
                            'day': day,
                            'id': '1'}))

        c = Client()
        c.login(username='mentor', password='passwd')
        response = c.get(edit_report_url, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        fake_messages.error.assert_called_once_with(
            mock.ANY, 'Permission denied.')

    def test_get_edit_non_existing_page_admin(self):
        """Get edit page for a report that does not exist as admin."""

        year, month, day = datetime.datetime.now().strftime('%d %B %Y').split()
        edit_report_url = (
            reverse('reports_ng_edit_report',
                    kwargs={'display_name': self.user.userprofile.display_name,
                            'year': year,
                            'month': month,
                            'day': day,
                            'id': '1'}))
        UserFactory.create(username='admin', groups=['Admin', 'Rep'])
        c = Client()
        c.login(username='admin', password='passwd')
        response = c.get(edit_report_url, follow=True)
        self.assertTemplateUsed(response, '404.html')

    def test_get_edit_page_admin(self):
        """Get edit page for a report as admin."""

        year, month, day = datetime.datetime.now().strftime('%d %B %Y').split()
        edit_report_url = (
            reverse('reports_ng_edit_report',
                    kwargs={'display_name': self.user.userprofile.display_name,
                            'year': year,
                            'month': month,
                            'day': day,
                            'id': '1'}))
        UserFactory.create(username='admin', groups=['Admin', 'Rep'])
        # Force a report with the same pk as the edit url
        NGReportFactory.create(user=self.user, pk=1)
        c = Client()
        c.login(username='admin', password='passwd')
        response = c.get(edit_report_url, follow=True)
        self.assertTemplateUsed(response, 'edit_ng_report.html')

    @mock.patch('remo.reports.views.messages')
    def test_add_report(self, fake_messages):
        """Test adding a new report."""

        now = datetime.datetime.now().strftime('%d %B %Y')
        new_report_url = reverse('reports_new_ng_report')
        activity = ActivityFactory.create()
        post_data = {'activity': activity.id,
                     'longitude': 123.123,
                     'latitude': 456.456,
                     'location': 'MyLocation',
                     'link': 'http://www.example.com/',
                     'functional_areas': [7, 15],
                     'report_date': now}

        c = Client()
        c.login(username='rep', password='passwd')
        response = c.post(new_report_url, post_data, follow=True)
        report = NGReport.objects.get(user=self.user)
        eq_(response.request['PATH_INFO'], report.get_absolute_url())
        fake_messages.success.assert_called_once_with(
            mock.ANY, 'Report successfully created.')

    @mock.patch('remo.reports.views.messages')
    def test_edit_report(self, fake_messages):
        """Test editing an already saved report as owner."""

        report = NGReportFactory.create(random_functional_areas=True,
                                        user=self.user)
        activity = ActivityFactory.create()
        campaign = CampaignFactory.create()
        post_data = {'activity': activity.id,
                     'campaign': campaign.id,
                     'longitude': 123.123,
                     'latitude': 456.456,
                     'location': 'MyLocation',
                     'link': 'http://www.example.com/',
                     'functional_areas': [7, 15],
                     'report_date': '14 November 2013'}

        c = Client()
        c.login(username='rep', password='passwd')
        response = c.post(report.get_absolute_edit_url(), post_data,
                          follow=True)
        report = NGReport.objects.get(pk=report.id)
        eq_(response.request['PATH_INFO'], report.get_absolute_url())
        fake_messages.success.assert_called_once_with(
            mock.ANY, 'Report successfully updated.')

        excluded = ['functional_areas', 'report_date',
                    'activity', 'campaign', 'user', 'mentor']
        # Test saved fields
        for field in set(post_data).difference(set(excluded)):
            if getattr(report, field, None):
                eq_(getattr(report, field), post_data[field])
        # Test excluded fields
        eq_(datetime.datetime.strptime(post_data['report_date'],
                                       '%d %B %Y').date(),
            report.report_date)
        eq_(post_data['activity'], report.activity.id)
        eq_(post_data['campaign'], report.campaign.id)
        eq_(len(set(post_data['functional_areas']).intersection(
            report.functional_areas.all().values_list('id', flat=True))), 2)

    @mock.patch('remo.base.decorators.messages')
    def test_edit_report_no_owner(self, fake_messages):
        """Test editing an already saved report without being the owner."""

        UserFactory.create(username='rep1', groups=['Rep'],
                           userprofile__mentor=self.mentor)
        report = NGReportFactory.create(random_functional_areas=True,
                                        user=self.user)
        c = Client()
        c.login(username='rep1', password='passwd')
        response = c.get(report.get_absolute_edit_url(), follow=True)
        self.assertTemplateUsed(response, 'main.html')
        fake_messages.error.assert_called_once_with(
            mock.ANY, 'Permission denied.')


class DeleteNGReportTests(TestCase):
    """Tests related to New Generation Reports delete View."""

    def setUp(self):
        """Setup tests."""

        # Create waffle flag
        Flag.objects.create(name='reports_ng_report', everyone=True)
        # Give permissions to admin group
        group = Group.objects.get(name='Admin')
        permissions = Permission.objects.filter(codename__icontains='ngreport')
        for perm in permissions:
            group.permissions.add(perm)
        self.mentor = UserFactory.create(username='mentor', groups=['Mentor'])
        self.user = UserFactory.create(username='rep', groups=['Rep'],
                                       userprofile__mentor=self.mentor)
        self.report = NGReportFactory.create(random_functional_areas=True,
                                             user=self.user)

    @mock.patch('remo.base.decorators.messages')
    def test_delete_as_anonymous(self, fake_messages):
        """Delete a saved report as anonymous user."""

        c = Client()
        response = c.get(self.report.get_absolute_delete_url(), follow=True)
        self.assertTemplateUsed(response, 'main.html')
        fake_messages.warning.assert_called_once_with(
            mock.ANY, 'Please login.')

    @mock.patch('remo.base.decorators.messages')
    def test_delete_report_mentor(self, fake_messages):
        """Delete a saved report as owner's mentor."""

        c = Client()
        c.login(username='mentor', password='passwd')
        response = c.get(self.report.get_absolute_delete_url(), follow=True)
        self.assertTemplateUsed(response, 'main.html')
        fake_messages.error.assert_called_once_with(
            mock.ANY, 'Permission denied.')

    @mock.patch('remo.base.decorators.messages')
    def test_delete_report_rep(self, fake_messages):
        """Delete a saved report as another rep."""

        UserFactory.create(username='rep1', groups=['Rep'],
                           userprofile__mentor=self.mentor)
        c = Client()
        c.login(username='rep1', password='passwd')
        response = c.get(self.report.get_absolute_delete_url(), follow=True)
        self.assertTemplateUsed(response, 'main.html')
        fake_messages.error.assert_called_once_with(
            mock.ANY, 'Permission denied.')

    def test_delete_report_owner(self):
        """Delete a saved report as owner."""

        c = Client()
        c.login(username='rep', password='passwd')
        response = c.post(self.report.get_absolute_delete_url(), follow=True)
        self.assertTemplateUsed(response, 'profiles_view.html')
        eq_(NGReport.objects.filter(pk=self.report.id).count(), 0)

    def test_delete_report_admin(self):
        """Delete a saved report as admin."""

        UserFactory.create(username='admin', groups=['Admin', 'Rep'])
        c = Client()
        c.login(username='admin', password='passwd')
        response = c.post(self.report.get_absolute_delete_url(), follow=True)
        self.assertTemplateUsed(response, 'profiles_view.html')
        eq_(NGReport.objects.filter(pk=self.report.id).count(), 0)
