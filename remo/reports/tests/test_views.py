import datetime

from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.test.client import Client

import mock
from mock import patch
from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase, requires_login, requires_permission
from remo.profiles.tests import FunctionalAreaFactory, UserFactory
from remo.reports.models import NGReport, NGReportComment
from remo.reports.tests import NGReportFactory, NGReportCommentFactory


class EditNGReportTests(RemoTestCase):
    """Tests related to New Generation Reports edit View."""

    def test_new_report_initial_data(self):
        user = UserFactory.create(groups=['Mentor'], userprofile__city='City',
                                  userprofile__region='Region',
                                  userprofile__country='Country',
                                  userprofile__lat=0,
                                  userprofile__lon=90)
        response = self.get(url=reverse('reports_new_ng_report'),
                            user=user)
        initial = response.context['report_form'].initial
        eq_(initial['location'], 'City, Region, Country')
        eq_(initial['latitude'], 0)
        eq_(initial['longitude'], 90)

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

    @patch('remo.reports.views.messages.warning')
    def test_get_uneditable(self, messages_mock):
        report = NGReportFactory.create(activity__name='Month recap')
        self.get(url=report.get_absolute_edit_url(),
                 user=report.user, follow=True)
        messages_mock.assert_called_with(
            mock.ANY, 'You cannot edit this report.')

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

    def test_get_uneditable(self):
        report = NGReportFactory.create(activity__name='Created an Event')
        response = self.get(url=report.get_absolute_url(), user=report.user)
        ok_(not response.context['editable'])


class DeleteNGReportCommentTests(RemoTestCase):
    """Tests related to comment deletion."""

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

    def test_list(self):
        """Test view report list page."""
        report = NGReportFactory.create()
        response = self.get(reverse('list_ng_reports'))
        self.assertTemplateUsed(response, 'list_ng_reports.html')
        eq_(response.context['pageheader'], 'Activities for Reps')
        eq_(response.status_code, 200)
        eq_(set(response.context['reports'].object_list),
            set([report]))

    def test_list_rep(self):
        """Test page header context for rep."""
        user = UserFactory.create(groups=['Rep'], first_name='Foo',
                                  last_name='Bar')
        name = user.userprofile.display_name
        report = NGReportFactory.create(user=user)
        NGReportFactory.create()
        response = self.get(url=reverse('list_ng_reports_rep',
                                        kwargs={'rep': name}), user=user)
        eq_(response.context['pageheader'], 'Activities for Foo Bar')
        eq_(set(response.context['reports'].object_list),
            set([report]), 'Other Rep reports are listed')

    def test_list_mentor(self):
        """Test page header context for mentor."""
        mentor = UserFactory.create(groups=['Mentor'], first_name='Foo',
                                    last_name='Bar')
        name = mentor.userprofile.display_name

        report_1 = NGReportFactory.create(mentor=mentor)
        report_2 = NGReportFactory.create(mentor=mentor)
        NGReportFactory.create()
        response = self.get(url=reverse('list_ng_reports_mentor',
                                        kwargs={'mentor': name}), user=mentor)
        msg = 'Activities for Reps mentored by Foo Bar'
        eq_(response.context['pageheader'], msg)
        eq_(set(response.context['reports'].object_list),
            set([report_1, report_2]), 'Other Mentor reports are listed')

    def test_get_invalid_order(self):
        """Test get invalid sort order."""
        response = self.get(url=reverse('list_ng_reports'),
                            data={'sort_key': 'invalid'})
        eq_(response.context['sort_key'], 'report_date_desc')

    def test_future_not_listed(self):
        report = NGReportFactory.create()
        NGReportFactory.create(report_date=datetime.date(2999, 1, 1))
        response = self.get(reverse('list_ng_reports'))
        eq_(set(response.context['reports'].object_list),
            set([report]))

    def test_functional_area_list(self):
        functional_area_1 = FunctionalAreaFactory.create()
        functional_area_2 = FunctionalAreaFactory.create()
        report = NGReportFactory.create(functional_areas=[functional_area_1])
        NGReportFactory.create(functional_areas=[functional_area_2])
        url = reverse('list_ng_reports_functional_area',
                      kwargs={'functional_area_slug': functional_area_1.slug})
        response = self.get(url=url)
        eq_(set(response.context['reports'].object_list), set([report]))

    def test_rep_functional_area_list(self):
        user = UserFactory.create(groups=['Rep'])
        functional_area = FunctionalAreaFactory.create()
        report = NGReportFactory.create(user=user,
                                        functional_areas=[functional_area])
        NGReportFactory.create(functional_areas=[functional_area])
        url = reverse('list_ng_reports_rep_functional_area',
                      kwargs={'functional_area_slug': functional_area.slug,
                              'rep': user.userprofile.display_name})
        response = self.get(url=url)
        eq_(set(response.context['reports'].object_list), set([report]))

    def test_mentor_functional_area_list(self):
        mentor = UserFactory.create(groups=['Mentor'])
        functional_area = FunctionalAreaFactory.create()
        report = NGReportFactory.create(mentor=mentor,
                                        functional_areas=[functional_area])
        NGReportFactory.create(functional_areas=[functional_area])
        url = reverse('list_ng_reports_mentor_functional_area',
                      kwargs={'functional_area_slug': functional_area.slug,
                              'mentor': mentor.userprofile.display_name})
        response = self.get(url=url)
        eq_(set(response.context['reports'].object_list), set([report]))


class LegacyReportingTests(RemoTestCase):
    def test_old_report_redirect(self):
        """Test old report url redirects to list of reports for that month."""
        user = UserFactory.create(groups=['Rep'])
        report_date = datetime.date(2011, 01, 05)
        NGReportFactory.create_batch(3, user=user, report_date=report_date)

        display_name = user.userprofile.display_name
        url = reverse('reports_ng_view_report',
                      kwargs={'display_name': display_name,
                              'month': 'January',
                              'year': 2011})
        response = self.get(url, follow=True)
        redirect_url = '/reports/rep/%s/?year=2011&month=January'
        self.assertRedirects(response, redirect_url % display_name)
        eq_(response.context['number_of_reports'], 3)
