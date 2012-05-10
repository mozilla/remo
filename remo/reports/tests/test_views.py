import datetime

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client
from nose.tools import eq_, nottest
from test_utils import TestCase

from remo.base.utils import go_back_n_months
from remo.reports.models import Report, ReportComment
from remo.reports.views import LIST_REPORTS_VALID_SHORTS


class ViewsTest(TestCase):
    """Tests related to Reports Views."""
    fixtures = ['demo_users.json', 'demo_reports.json']

    def setUp(self):
        """Setup tests."""
        self.user = User.objects.get(username='rep')
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
            response = c.get(reverse('reports_list_reports') +
                             '&sort_key=%s' % sort_key)
            self.assertTemplateUsed(response, 'reports_list.html')

        # Test pagination.
        response = c.get(reverse('reports_list_reports') + '&page=1')
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
        Report.objects.create(user=self.user, empty=True,
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
