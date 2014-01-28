import datetime

from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.test.client import Client

import mock
from funfactory.helpers import urlparams
from mock import patch
from nose.tools import eq_, ok_
from test_utils import TestCase
from waffle import Flag

from remo.base.utils import go_back_n_months
from remo.base.tests import RemoTestCase, requires_login, requires_permission
from remo.profiles.tests import UserFactory
from remo.reports.models import NGReport, NGReportComment, ReportComment
from remo.reports.tests import (NGReportFactory, NGReportCommentFactory,
                                ReportCommentFactory, ReportFactory)
from remo.reports.views import (LIST_NG_REPORTS_VALID_SORTS,
                                LIST_REPORTS_VALID_SORTS)


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

        for sort_key in LIST_REPORTS_VALID_SORTS:
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
        ok_(not ReportComment.objects.filter(pk=9).exists())

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
        ok_(not ReportComment.objects.filter(pk=10).exists())


# New generation reports tests
class EditNGReportTests(RemoTestCase):
    """Tests related to New Generation Reports edit View."""

    def setUp(self):
        """Setup tests."""
        # Create waffle flag
        Flag.objects.create(name='reports_ng_report', everyone=True)

    def test_get_as_owner(self):
        report = NGReportFactory.create()
        response = self.get(url=report.get_absolute_edit_url(),
                            user=report.user)
        eq_(response.context['report'], report)
        self.assertTemplateUsed('edit_ng_report.html')

    def test_get_as_mentor(self):
        user = UserFactory.create(groups=['Mentor'])
        report = NGReportFactory.create()
        response = self.get(url=report.get_absolute_edit_url(),
                            user=user)
        eq_(response.context['report'], report)
        self.assertTemplateUsed('edit_ng_report.html')

    def test_get_as_admin(self):
        user = UserFactory.create(groups=['Admin'])
        report = NGReportFactory.create()
        response = self.get(url=report.get_absolute_edit_url(),
                            user=user)
        eq_(response.context['report'], report)
        self.assertTemplateUsed('edit_ng_report.html')

    @requires_permission()
    def test_get_as_other_rep(self):
        user = UserFactory.create()
        report = NGReportFactory.create()
        self.get(url=report.get_absolute_edit_url(), user=user)

    @requires_login()
    def test_get_as_anonymous(self):
        report = NGReportFactory.create()
        client = Client()
        client.get(report.get_absolute_edit_url())

    @patch('remo.reports.views.messages.success')
    @patch('remo.reports.views.redirect', wraps=redirect)
    @patch('remo.reports.views.forms.NGReportForm')
    @patch('remo.reports.models.NGReport.get_absolute_url')
    def test_create_new_report(self, get_absolute_url_mock, form_mock,
                               redirect_mock, messages_mock):
        form_mock.is_valid.return_value = True
        get_absolute_url_mock.return_value = 'main'
        user = UserFactory.create()
        response = self.post(url=reverse('reports_new_ng_report'),
                             user=user)
        eq_(response.status_code, 200)
        messages_mock.assert_called_with(
            mock.ANY, 'Report successfully created.')
        redirect_mock.assert_called_with('main')
        ok_(form_mock().save.called)

    @patch('remo.reports.views.messages.success')
    @patch('remo.reports.views.redirect', wraps=redirect)
    @patch('remo.reports.views.forms.NGReportForm')
    @patch('remo.reports.models.NGReport.get_absolute_url')
    def test_update_report(self, get_absolute_url_mock, form_mock,
                           redirect_mock, messages_mock):
        form_mock.is_valid.return_value = True
        get_absolute_url_mock.return_value = 'main'
        report = NGReportFactory.create()
        response = self.post(url=report.get_absolute_edit_url(),
                             user=report.user)
        eq_(response.status_code, 200)
        messages_mock.assert_called_with(
            mock.ANY, 'Report successfully updated.')
        redirect_mock.assert_called_with('main')
        ok_(form_mock().save.called)

    def test_get_non_existing_report(self):
        user = UserFactory.create()
        url = (reverse('reports_ng_edit_report',
                       kwargs={'display_name': user.userprofile.display_name,
                               'year': 3000,
                               'month': 'March',
                               'day': 1,
                               'id': 1}))
        response = self.get(url=url, user=user)
        self.assertTemplateUsed('404.html')
        eq_(response.status_code, 404)


class DeleteNGReportTests(RemoTestCase):
    def setUp(self):
        Flag.objects.create(name='reports_ng_report', everyone=True)

    @patch('remo.reports.views.redirect', wraps=redirect)
    def test_as_owner(self, redirect_mock):
        report = NGReportFactory.create()
        self.post(user=report.user, url=report.get_absolute_delete_url())
        ok_(not NGReport.objects.filter(pk=report.id).exists())
        redirect_mock.assert_called_with('profiles_view_my_profile')

    @requires_login()
    def test_as_anonymous(self):
        report = NGReportFactory.create()
        client = Client()
        client.post(report.get_absolute_delete_url(), data={})
        ok_(NGReport.objects.filter(pk=report.id).exists())

    @requires_permission()
    def test_as_other_rep(self):
        user = UserFactory.create()
        report = NGReportFactory.create()
        self.post(user=user, url=report.get_absolute_delete_url())
        ok_(NGReport.objects.filter(pk=report.id).exists())

    def test_get(self):
        report = NGReportFactory.create()
        self.get(user=report.user, url=report.get_absolute_delete_url())
        ok_(NGReport.objects.filter(pk=report.id).exists())

    @patch('remo.reports.views.redirect', wraps=redirect)
    def test_as_mentor(self, redirect_mock):
        user = UserFactory.create(groups=['Mentor'])
        report = NGReportFactory.create()
        self.post(user=user, url=report.get_absolute_delete_url())
        ok_(not NGReport.objects.filter(pk=report.id).exists())
        redirect_mock.assert_called_with(
            'profiles_view_profile',
            display_name=report.user.userprofile.display_name)

    @patch('remo.reports.views.redirect', wraps=redirect)
    def test_as_admin(self, redirect_mock):
        user = UserFactory.create(groups=['Admin'])
        report = NGReportFactory.create()
        self.post(user=user, url=report.get_absolute_delete_url())
        ok_(not NGReport.objects.filter(pk=report.id).exists())
        redirect_mock.assert_called_with(
            'profiles_view_profile',
            display_name=report.user.userprofile.display_name)


class ViewNGReportTests(RemoTestCase):
    """Tests related to New Generation Reports view_ng_report View."""

    def setUp(self):
        """Setup tests."""
        # Create waffle flag
        Flag.objects.create(name='reports_ng_report', everyone=True)

    def test_get(self):
        report = NGReportFactory.create()
        response = self.get(url=report.get_absolute_url(),
                            user=report.user)
        eq_(response.context['report'], report)
        self.assertTemplateUsed('view_ng_report.html')

    @patch('remo.reports.views.messages.success')
    @patch('remo.reports.views.forms.NGReportCommentForm')
    def test_post_a_comment(self, form_mock, messages_mock):
        user = UserFactory.create()
        report = NGReportFactory.create(user=user)
        form_mock.is_valid.return_value = True
        response = self.post(url=report.get_absolute_url(),
                             user=user)
        eq_(response.status_code, 200)
        messages_mock.assert_called_with(
            mock.ANY, 'Comment saved successfully.')
        ok_(form_mock().save.called)
        eq_(response.context['report'], report)
        self.assertTemplateUsed('view_ng_report.html')

    @patch('remo.reports.views.messages.error')
    @patch('remo.reports.views.forms.NGReportCommentForm')
    @patch('remo.reports.views.redirect', wraps=redirect)
    def test_post_a_comment_anonymous(self, redirect_mock, form_mock,
                                      messages_mock):
        form_mock.is_valid.return_value = True
        report = NGReportFactory.create()
        c = Client()
        c.post(report.get_absolute_url(), data={})
        ok_(not NGReportComment.objects.filter(report=report).exists())

        messages_mock.assert_called_with(mock.ANY, 'Permission denied.')
        redirect_mock.assert_called_with('main')


class DeleteNGReportCommentTests(RemoTestCase):
    """Tests related to comment deletion."""
    def setUp(self):
        Flag.objects.create(name='reports_ng_report', everyone=True)

    @patch('remo.reports.views.redirect', wraps=redirect)
    def test_as_owner(self, redirect_mock):
        report = NGReportFactory.create()
        report_comment = NGReportCommentFactory.create(report=report)
        self.post(user=report.user,
                  url=report_comment.get_absolute_delete_url())
        ok_(not NGReportComment.objects.filter(pk=report_comment.id).exists())
        redirect_mock.assert_called_with(report.get_absolute_url())

    @requires_login()
    def test_as_anonymous(self):
        report = NGReportFactory.create()
        report_comment = NGReportCommentFactory.create(report=report)
        client = Client()
        client.post(report_comment.get_absolute_delete_url(), data={})
        ok_(NGReportComment.objects.filter(pk=report_comment.id).exists())

    @requires_permission()
    def test_as_other_rep(self):
        user = UserFactory.create()
        report = NGReportFactory.create()
        report_comment = NGReportCommentFactory.create(report=report)
        self.post(user=user, url=report_comment.get_absolute_delete_url())
        ok_(NGReportComment.objects.filter(pk=report_comment.id).exists())

    def test_get(self):
        report = NGReportFactory.create()
        report_comment = NGReportCommentFactory.create(report=report)
        self.get(user=report.user,
                 url=report_comment.get_absolute_delete_url())
        ok_(NGReportComment.objects.filter(pk=report_comment.id).exists())

    @patch('remo.reports.views.redirect', wraps=redirect)
    def test_as_mentor(self, redirect_mock):
        user = UserFactory.create(groups=['Mentor'])
        report = NGReportFactory.create()
        report_comment = NGReportCommentFactory.create(report=report)
        self.post(user=user, url=report_comment.get_absolute_delete_url())
        ok_(not NGReportComment.objects.filter(pk=report_comment.id).exists())
        redirect_mock.assert_called_with(report.get_absolute_url())

    @patch('remo.reports.views.redirect', wraps=redirect)
    def test_as_admin(self, redirect_mock):
        user = UserFactory.create(groups=['Admin'])
        report = NGReportFactory.create()
        report_comment = NGReportCommentFactory.create(report=report)
        self.post(user=user, url=report_comment.get_absolute_delete_url())
        ok_(not NGReportComment.objects.filter(pk=report_comment.id).exists())
        redirect_mock.assert_called_with(report.get_absolute_url())


class ListNGReportTests(RemoTestCase):
    """Tests related to report listing."""
    def setUp(self):
        Flag.objects.create(name='reports_ng_report', everyone=True)

    def test_view_reports_list(self):
        """Test view report list page."""
        response = self.get(reverse('ng_reports_list_reports'))
        self.assertTemplateUsed(response, 'ng_reports_list.html')

        for sort_key in LIST_NG_REPORTS_VALID_SORTS:
            response = self.get(urlparams(reverse('ng_reports_list_reports'),
                                          sort_key=sort_key))
            self.assertTemplateUsed(response, 'ng_reports_list.html')

        # Test pagination.
        response = self.get(urlparams(reverse('ng_reports_list_reports'),
                                      page=1))
        self.assertTemplateUsed(response, 'ng_reports_list.html')

    def test_page_header(self):
        """Test page header context."""
        user = UserFactory.create(groups=['Rep'], first_name='Foo',
                                  last_name='Bar')
        name = user.userprofile.display_name
        response = self.get(url=reverse('ng_reports_list_reports'),
                            user=name)
        eq_(response.context['pageheader'], 'Activities for Foo Bar')
