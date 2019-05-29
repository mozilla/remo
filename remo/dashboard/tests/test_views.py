from datetime import timedelta

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.utils.timezone import now

import mock
from nose.tools import eq_, ok_

from remo.base.templatetags.helpers import urlparams
from remo.base.tests import RemoTestCase
from remo.dashboard.models import ActionItem
from remo.events.tests import EventFactory
from remo.profiles.tests import FunctionalAreaFactory, UserFactory
from remo.remozilla.models import Bug
from remo.remozilla.tests import BugFactory
from remo.reports import ACTIVITY_EVENT_CREATE
from remo.reports.tests import ActivityFactory, NGReportFactory


class ViewsTest(RemoTestCase):
    """Test views."""

    def setUp(self):
        self.settings_data = {'receive_email_on_add_comment': True}
        self.user_edit_settings_url = reverse('edit_settings')
        self.failed_url = urlparams(settings.LOGIN_REDIRECT_URL_FAILURE, bid_login_failed=1)

    def test_view_dashboard_page(self):
        """Get dashboard page."""
        c = Client()

        # Get as anonymous user.
        response = c.get(reverse('dashboard'), follow=True)
        eq_(response.status_code, 200)
        self.assertJinja2TemplateUsed(response, 'main.jinja')

        # Get as logged in rep.
        rep = UserFactory.create(groups=['Rep'])
        with self.login(rep) as client:
            response = client.get(reverse('dashboard'))
        eq_(response.status_code, 200)
        self.assertJinja2TemplateUsed(response, 'dashboard_reps.jinja')

        # Get as logged in mentor.
        mentor = UserFactory.create(groups=['Mentor'])
        with self.login(mentor) as client:
            response = client.get(reverse('dashboard'))
        eq_(response.status_code, 200)
        self.assertJinja2TemplateUsed(response, 'dashboard_reps.jinja')

        # Get as logged in counselor.
        councelor = UserFactory.create(groups=['Council'])
        with self.login(councelor) as client:
            response = client.get(reverse('dashboard'))
        eq_(response.status_code, 200)
        self.assertJinja2TemplateUsed(response, 'dashboard_reps.jinja')

    @mock.patch('remo.dashboard.views.messages.success')
    def test_email_my_mentees_mentor_with_send_True(self, faked_message):
        """Email mentees when mentor and checkbox is checked."""
        mentor = UserFactory.create(groups=['Mentor'])
        rep = UserFactory.create(groups=['Rep'], userprofile__mentor=mentor)
        data = {'%s' % (rep.id): 'True',
                'subject': 'This is subject',
                'body': ('This is my body\n',
                         'Multiline of course')}
        with self.login(mentor) as client:
            response = client.post(reverse('email_mentees'), data, follow=True)
        self.assertJinja2TemplateUsed(response, 'dashboard_reps.jinja')
        ok_(faked_message.called)
        eq_(faked_message.call_args[0][1], 'Email sent successfully.')
        eq_(len(mail.outbox), 1)
        eq_(len(mail.outbox[0].to), 1)
        eq_(len(mail.outbox[0].cc), 1)

    @mock.patch('remo.dashboard.views.messages.error')
    def test_email_my_mentees_mentor_with_send_False(self, faked_message):
        """Email mentees when mentor and checkbox is not checked."""
        mentor = UserFactory.create(groups=['Mentor'])
        rep = UserFactory.create(groups=['Rep'], userprofile__mentor=mentor)
        data = {'%s' % (rep.id): 'False',
                'subject': 'This is subject',
                'body': ('This is my body\n',
                         'Multiline of course')}
        with self.login(mentor) as client:
            response = client.post(reverse('email_mentees'), data, follow=True)
        self.assertJinja2TemplateUsed(response, 'dashboard_reps.jinja')
        ok_(faked_message.called)
        eq_(faked_message.call_args[0][1],
            'Email not sent. Please select at least one recipient.')
        eq_(len(mail.outbox), 0)

    @mock.patch('remo.dashboard.views.messages.error')
    def test_email_my_mentees_rep(self, faked_message):
        """Email mentees when rep.

        Must fail since Rep doesn't have mentees.
        """
        rep = UserFactory.create(groups=['Rep'])
        data = {'subject': 'This is subject',
                'body': ('This is my body',
                         'Multiline ofcourse')}
        with self.login(rep) as client:
            response = client.post(reverse('email_mentees'), data, follow=True)
        self.assertJinja2TemplateUsed(response, 'main.jinja')
        ok_(faked_message.called)
        eq_(faked_message.call_args[0][1], 'Permission denied.')
        eq_(len(mail.outbox), 0)

    @mock.patch('remo.dashboard.views.messages.success')
    def test_email_reps_as_mozillian(self, faked_message):
        """Email all the reps associated with a functional area."""
        mozillian = UserFactory.create(groups=['Mozillians'])
        area = FunctionalAreaFactory.create()
        UserFactory.create(groups=['Rep'],
                           userprofile__functional_areas=[area])
        data = {'subject': 'This is subject',
                'body': 'This is my body\n Multiline of course',
                'functional_area': area.id}
        with self.login(mozillian) as client:
            response = client.post(reverse('dashboard'), data, follow=True)
        ok_(faked_message.called)
        eq_(faked_message.call_args[0][1], 'Email sent successfully.')
        eq_(len(mail.outbox), 1)
        self.assertJinja2TemplateUsed(response, 'dashboard_mozillians.jinja')


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
        with self.login(user) as client:
            response = client.get(reverse('list_action_items'), user=user)
        self.assertJinja2TemplateUsed(response, 'list_action_items.jinja')
        eq_(response.context['pageheader'], 'My Action Items')
        eq_(response.status_code, 200)
        eq_(set(response.context['objects'].object_list), set([item]))


class KPIDashboardTest(RemoTestCase):
    """Test dashboard KPIs and stats."""

    def setUp(self):
        ActivityFactory.create(name=ACTIVITY_EVENT_CREATE)

    def test_base(self):
        response = Client().get(reverse('kpi'))
        eq_(response.status_code, 200)
        self.assertJinja2TemplateUsed(response, 'kpi.jinja')

    def test_overview(self):
        UserFactory.create_batch(10, groups=['Rep'])
        NGReportFactory.create_batch(12)

        # Past events
        EventFactory.create_batch(5)
        # Current and future events
        EventFactory.create_batch(10, start=now() + timedelta(days=3),
                                  end=now() + timedelta(days=4))

        response = Client().get(reverse('kpi'))

        eq_(response.status_code, 200)
        self.assertJinja2TemplateUsed(response, 'kpi.jinja')
        eq_(response.context['reps_count'], 10)
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
            NGReportFactory.create(user=user, report_date=now().date() - active)
            NGReportFactory.create(user=user, report_date=now().date() + active)

            # Activities in future and past 4+ weeks
            NGReportFactory.create(user=user, report_date=now().date() - inactive_low)
            NGReportFactory.create(user=user, report_date=now().date() + inactive_low)

            # Activities in future and past 8+ weeks
            NGReportFactory.create(user=user, report_date=now().date() - inactive_high)
            NGReportFactory.create(user=user, report_date=now().date() + inactive_high)

        for user in inactive_low_reps:
            # Activities in future and past 4+ weeks
            NGReportFactory.create(user=user, report_date=now().date() - inactive_low)
            NGReportFactory.create(user=user, report_date=now().date() + inactive_low)

            # Activities in future and past 8+ weeks
            NGReportFactory.create(user=user, report_date=now().date() - inactive_high)
            NGReportFactory.create(user=user, report_date=now().date() + inactive_high)

        for user in inactive_high_reps:
            # Activities in future and past 8+ weeks
            NGReportFactory.create(user=user, report_date=now().date() - inactive_high)
            NGReportFactory.create(user=user, report_date=now().date() + inactive_high)

        response = Client().get(reverse('kpi'))

        eq_(response.status_code, 200)
        self.assertJinja2TemplateUsed(response, 'kpi.jinja')
        eq_(response.context['active_users'], 5)
        eq_(response.context['inactive_low_users'], 4)
        eq_(response.context['inactive_high_users'], 3)
