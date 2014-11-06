from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.utils.timezone import now

from funfactory.helpers import urlparams
from nose.tools import eq_, ok_
from test_utils import TestCase

from remo.base.tests import RemoTestCase
from remo.dashboard.models import ActionItem
from remo.events.tests import EventFactory
from remo.profiles.tests import FunctionalAreaFactory, UserFactory
from remo.remozilla.models import Bug
from remo.remozilla.tests import BugFactory
from remo.reports.tests import NGReportFactory


class ViewsTest(TestCase):
    """Test views."""
    fixtures = ['demo_users.json']

    def setUp(self):
        self.settings_data = {'receive_email_on_add_comment': True}
        self.user_edit_settings_url = reverse('edit_settings')
        self.failed_url = urlparams(settings.LOGIN_REDIRECT_URL_FAILURE,
                                    bid_login_failed=1)

    def test_view_dashboard_page(self):
        """Get dashboard page."""
        c = Client()

        # Get as anonymous user.
        response = c.get(reverse('dashboard'), follow=True)
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'main.html')

        # Get as logged in rep.
        c.login(username='rep', password='passwd')
        response = c.get(reverse('dashboard'))
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard_reps.html')

        # Get as logged in mentor.
        c.login(username='mentor', password='passwd')
        response = c.get(reverse('dashboard'))
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard_reps.html')

        # Get as logged in counselor.
        c.login(username='counselor', password='passwd')
        response = c.get(reverse('dashboard'))
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard_reps.html')

    def test_email_my_mentees_mentor_with_send_True(self):
        """Email mentees when mentor and checkbox is checked."""
        c = Client()
        c.login(username='mentor', password='passwd')
        rep1 = User.objects.get(first_name='Nick')
        data = {'%s' % (rep1.id): 'True',
                'subject': 'This is subject',
                'body': ('This is my body\n',
                         'Multiline of course')}
        response = c.post(reverse('email_mentees'), data, follow=True)
        self.assertTemplateUsed(response, 'dashboard_reps.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')
        eq_(len(mail.outbox), 1)
        eq_(len(mail.outbox[0].to), 1)
        eq_(len(mail.outbox[0].cc), 1)

    def test_email_my_mentees_mentor_with_send_False(self):
        """Email mentees when mentor and checkbox is not checked."""
        c = Client()
        c.login(username='mentor', password='passwd')
        rep1 = User.objects.get(first_name='Nick')
        data = {'%s' % (rep1.id): 'False',
                'subject': 'This is subject',
                'body': ('This is my body\n',
                         'Multiline of course')}
        response = c.post(reverse('email_mentees'), data, follow=True)
        self.assertTemplateUsed(response, 'dashboard_reps.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')
        eq_(len(mail.outbox), 0)

    def test_email_my_mentees_rep(self):
        """Email mentees when rep.

        Must fail since Rep doesn't have mentees.
        """
        c = Client()
        c.login(username='rep', password='passwd')
        data = {'subject': 'This is subject',
                'body': ('This is my body',
                         'Multiline ofcourse')}
        response = c.post(reverse('email_mentees'), data, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')
        eq_(len(mail.outbox), 0)

    def test_email_reps_as_mozillian(self):
        """Email all the reps associated with a functional area."""
        c = Client()
        area = FunctionalAreaFactory.create()
        UserFactory.create(groups=['Rep'],
                           userprofile__functional_areas=[area])
        c.login(username='mozillian1', password='passwd')
        data = {'subject': 'This is subject',
                'body': 'This is my body\n Multiline of course',
                'functional_area': area.id}
        response = c.post(reverse('dashboard'), data, follow=True)
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')
        eq_(len(mail.outbox), 1)
        self.assertTemplateUsed(response, 'dashboard_mozillians.html')


class StatsDashboardTest(RemoTestCase):
    """Test stats dashboard."""

    def test_base(self):
        response = self.get(reverse('stats_dashboard'))
        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'stats_dashboard.html')

    def test_overview(self):
        UserFactory.create_batch(10, groups=['Rep'])
        NGReportFactory.create_batch(12)

        # Past events
        EventFactory.create_batch(5)
        # Current and future events
        EventFactory.create_batch(10, start=now() + timedelta(days=3),
                                  end=now() + timedelta(days=4))

        response = self.get(reverse('stats_dashboard'))

        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'stats_dashboard.html')
        eq_(response.context['reps'], 10)
        eq_(response.context['past_events'], 5)
        eq_(response.context['future_events'], 10)
        eq_(response.context['activities'], 27)

    def test_inactive(self):
        reps = UserFactory.create_batch(12, groups=['Rep'])
        active = timedelta(days=5)
        inactive_low = timedelta(weeks=5)
        inactive_high = timedelta(weeks=9)

        active_reps = reps[:5]
        inactive_low_reps = reps[5:9]
        inactive_high_reps = reps[9:]

        for user in active_reps:
            # Activities in future and past 4 weeks
            NGReportFactory.create(user=user,
                                   report_date=now().date() - active)
            NGReportFactory.create(user=user,
                                   report_date=now().date() + active)

            # Activities in future and past 4+ weeks
            NGReportFactory.create(user=user,
                                   report_date=now().date() - inactive_low)
            NGReportFactory.create(user=user,
                                   report_date=now().date() + inactive_low)

            # Activities in future and past 8+ weeks
            NGReportFactory.create(user=user,
                                   report_date=now().date() - inactive_high)
            NGReportFactory.create(user=user,
                                   report_date=now().date() + inactive_high)

        for user in inactive_low_reps:
            # Activities in future and past 4+ weeks
            NGReportFactory.create(user=user,
                                   report_date=now().date() - inactive_low)
            NGReportFactory.create(user=user,
                                   report_date=now().date() + inactive_low)

            # Activities in future and past 8+ weeks
            NGReportFactory.create(user=user,
                                   report_date=now().date() - inactive_high)
            NGReportFactory.create(user=user,
                                   report_date=now().date() + inactive_high)

        for user in inactive_high_reps:
            # Activities in future and past 8+ weeks
            NGReportFactory.create(user=user,
                                   report_date=now().date() - inactive_high)
            NGReportFactory.create(user=user,
                                   report_date=now().date() + inactive_high)

        response = self.get(reverse('stats_dashboard'))

        eq_(response.status_code, 200)
        self.assertTemplateUsed(response, 'stats_dashboard.html')
        eq_(response.context['active_users'], 5)
        eq_(response.context['inactive_low_users'], 4)
        eq_(response.context['inactive_high_users'], 3)


class ListActionItemsTests(RemoTestCase):
    """Tests related to action items listing."""

    def test_list(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items)

        whiteboard = '[waiting receipts]'
        user = UserFactory.create(groups=['Rep'])
        bug = BugFactory.create(whiteboard=whiteboard, assigned_to=user)
        item = ActionItem.objects.get(content_type=model, object_id=bug.id)
        response = self.get(user=user, url=reverse('list_action_items'))
        self.assertTemplateUsed(response, 'list_action_items.html')
        eq_(response.context['pageheader'], 'My Action Items')
        eq_(response.status_code, 200)
        eq_(set(response.context['actions'].object_list),
            set([item]))
