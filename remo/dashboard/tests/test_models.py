# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now

import mock
from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.dashboard.models import ActionItem
from remo.events.models import Event
from remo.events.tasks import notify_event_owners_to_input_metrics
from remo.events.tests import EventFactory, EventMetricOutcomeFactory
from remo.profiles.models import UserProfile
from remo.profiles.tasks import (resolve_nomination_action_items,
                                 send_rotm_nomination_reminder)
from remo.profiles.tests import UserFactory
from remo.remozilla.models import Bug
from remo.remozilla.tests import BugFactory
from remo.reports import ACTIVITY_EVENT_ATTEND, ACTIVITY_EVENT_CREATE, RECRUIT_MOZILLIAN
from remo.reports.models import NGReport
from remo.reports.tests import ActivityFactory, NGReportFactory
from remo.voting.models import Poll
from remo.voting.tasks import resolve_action_items
from remo.voting.tests import PollFactory, VoteFactory


class RemozillaActionItems(RemoTestCase):
    """Test related to new action items created from bugzilla."""

    def test_waiting_receipts(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        whiteboard = '[waiting receipts]'
        user = UserFactory.create(groups=['Rep'])
        bug = BugFactory.create(whiteboard=whiteboard, assigned_to=user, summary=u'À summary')

        items = ActionItem.objects.filter(content_type=model, object_id=bug.id)
        eq_(items.count(), 1)
        eq_(items[0].name, 'Add receipts for ' + bug.summary)
        eq_(items[0].user, user)
        eq_(items[0].priority, ActionItem.NORMAL)

    def test_waiting_multiple_documents(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        whiteboard = '[waiting receipts][waiting report][waiting photos]'
        user = UserFactory.create(groups=['Rep'])
        bug = BugFactory.create(whiteboard=whiteboard, assigned_to=user)

        items = ActionItem.objects.filter(content_type=model, object_id=bug.id)
        eq_(items.count(), 3)

        namelist = ['Add receipts for ' + bug.summary,
                    'Add report for ' + bug.summary,
                    'Add photos for ' + bug.summary]

        for item in items:
            ok_(item.name in namelist)
            eq_(item.user, user)
            eq_(item.priority, ActionItem.NORMAL)

    def test_update_bug_whiteboard(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        whiteboard = '[waiting receipts][waiting report][waiting photos]'
        user = UserFactory.create(groups=['Rep'])
        bug = BugFactory.create(whiteboard=whiteboard, assigned_to=user)

        items = ActionItem.objects.filter(content_type=model)
        eq_(items.count(), 3)

        bug.whiteboard = ''
        bug.save()

        items = ActionItem.objects.filter(content_type=model, object_id=bug.id)
        for item in items:
            ok_(item.completed)
            ok_(item.resolved)

    def test_mentor_validation(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type=model)

        ok_(not items.exists())

        mentor = UserFactory.create(groups=['Rep', 'Mentor'])
        UserFactory.create(groups=['Rep'], userprofile__mentor=mentor)

        bug = BugFactory.create(pending_mentor_validation=True, assigned_to=mentor)

        items = ActionItem.objects.filter(content_type=model, object_id=bug.id)
        eq_(items.count(), 1)
        eq_(items[0].name, 'Waiting mentor validation for ' + bug.summary)
        eq_(items[0].user, mentor)
        eq_(items[0].priority, ActionItem.BLOCKER)

    def test_change_assigned_user(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        user_1 = UserFactory.create(groups=['Rep'])
        user_2 = UserFactory.create(groups=['Rep'])
        bug = BugFactory.create(assigned_to=user_1, pending_mentor_validation=True)
        item = ActionItem.objects.get(content_type=model, object_id=bug.id)
        eq_(item.user, user_1)

        bug.assigned_to = user_2
        bug.save()

        item = ActionItem.objects.get(content_type=model, object_id=bug.id)
        eq_(item.user, user_2)

    def test_resolve_mentor_validation(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        mentor = UserFactory.create(groups=['Rep', 'Mentor'])
        UserFactory.create(groups=['Rep'], userprofile__mentor=mentor)

        bug = BugFactory.create(pending_mentor_validation=True, assigned_to=mentor)

        items = ActionItem.objects.filter(content_type=model)
        eq_(items.count(), 1)
        eq_(items[0].name, 'Waiting mentor validation for ' + bug.summary)
        eq_(items[0].user, mentor)
        eq_(items[0].priority, ActionItem.BLOCKER)

        bug.pending_mentor_validation = False
        bug.save()

        items = ActionItem.objects.filter(content_type=model, object_id=bug.id)
        for item in items:
            ok_(item.completed)
            ok_(item.resolved)

    def test_needinfo(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type=model)

        ok_(not items.exists())

        needinfo = UserFactory.create(groups=['Rep'])
        user = UserFactory.create(groups=['Rep'])
        bug = BugFactory.create(assigned_to=user)
        bug.budget_needinfo.add(needinfo)

        items = ActionItem.objects.filter(content_type=model, object_id=bug.id)
        ok_(items.count(), 1)

        for item in items:
            eq_(item.name, 'Need info for ' + bug.summary)
            eq_(item.user, needinfo)
            ok_(item.priority, ActionItem.MINOR)

    def test_remove_needinfo(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type=model)

        user = UserFactory.create(groups=['Rep'])
        bug = BugFactory.create()
        bug.budget_needinfo.add(user)
        bug.budget_needinfo.clear()

        items = ActionItem.objects.filter(content_type=model, object_id=bug.id)
        for item in items:
            ok_(item.completed)
            ok_(item.resolved)

    def test_council_reviewer_assigned(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        user = UserFactory.create(groups=['Rep', 'Council'])
        bug = BugFactory.create(assigned_to=user, council_member_assigned=True)

        items = ActionItem.objects.filter(content_type=model, object_id=bug.id)
        eq_(items.count(), 1)
        eq_(items[0].name, 'Review budget request ' + bug.summary)
        eq_(items[0].user, user)
        eq_(items[0].priority, ActionItem.BLOCKER)

    def test_council_reviewer_removed(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        user = UserFactory.create(groups=['Council'])
        bug = BugFactory.create(assigned_to=user, council_member_assigned=True)

        bug.council_member_assigned = False
        bug.save()

        items = ActionItem.objects.filter(content_type=model, object_id=bug.id)
        for item in items:
            ok_(item.completed)
            ok_(item.resolved)

    def test_remove_assignee(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        user = UserFactory.create(groups=['Rep'])
        bug = BugFactory.create(pending_mentor_validation=True, assigned_to=user)

        items = ActionItem.objects.filter(content_type=model)
        eq_(items.count(), 1)
        eq_(items[0].name, 'Waiting mentor validation for ' + bug.summary)
        eq_(items[0].user, user)
        eq_(items[0].priority, ActionItem.BLOCKER)

        bug.assigned_to = None
        bug.save()

        items = ActionItem.objects.filter(content_type=model, object_id=bug.id)
        for item in items:
            ok_(item.resolved)
            ok_(not item.completed)


class VotingActionItems(RemoTestCase):
    def test_vote_action_item(self):
        model = ContentType.objects.get_for_model(Poll)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        council = Group.objects.get(name='Council')
        user = UserFactory.create(groups=['Council'])
        start = now() - timedelta(hours=3)
        poll = PollFactory.create(valid_groups=council, start=start)

        items = ActionItem.objects.filter(content_type=model, object_id=poll.id)
        eq_(items.count(), 1)

        for item in items:
            eq_(item.name, 'Cast your vote for ' + poll.name)
            eq_(item.user, user)
            ok_(item.priority, ActionItem.NORMAL)
            ok_(not item.completed)

    def test_budget_vote_action_item(self):
        model = ContentType.objects.get_for_model(Poll)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        council = Group.objects.get(name='Council')
        user = UserFactory.create(groups=['Council'])
        bug = BugFactory.create()

        start = now() - timedelta(hours=3)
        poll = PollFactory.create(valid_groups=council, automated_poll=True, bug=bug, start=start)

        items = ActionItem.objects.filter(content_type=model, object_id=poll.id)
        eq_(items.count(), 1)

        for item in items:
            eq_(item.name, 'Cast your vote for budget request ' + poll.bug.summary)
            eq_(item.user, user)
            ok_(item.priority, ActionItem.NORMAL)
            ok_(not item.completed)

    def test_future_vote_action_item(self):
        model = ContentType.objects.get_for_model(Poll)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        council = Group.objects.get(name='Council')
        start = now() + timedelta(hours=3)
        PollFactory.create(valid_groups=council, start=start)

        items = ActionItem.objects.filter(content_type=model)
        eq_(items.count(), 0)

    def test_resolve_vote_action_item(self):
        model = ContentType.objects.get_for_model(Poll)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        council = Group.objects.get(name='Council')
        user = UserFactory.create(groups=['Council'])
        start = now() - timedelta(hours=3)
        poll = PollFactory.create(valid_groups=council, start=start)
        VoteFactory.create(poll=poll, user=user)

        items = ActionItem.objects.filter(content_type=model, object_id=poll.id)
        eq_(items.count(), 1)

        for item in items:
            ok_(item.completed)
            ok_(item.resolved)

    def test_update_vote_due_date(self):
        model = ContentType.objects.get_for_model(Poll)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        council = Group.objects.get(name='Council')
        UserFactory.create(groups=['Council'])
        start = now() - timedelta(hours=3)
        poll = PollFactory.create(valid_groups=council, start=start)

        poll.end = poll.end + timedelta(days=4)
        poll.save()

        items = ActionItem.objects.filter(content_type=model, object_id=poll.id)
        eq_(items.count(), 1)

        for item in items:
            eq_(item.due_date, poll.end.date())

    def test_resolved_past_vote(self):
        model = ContentType.objects.get_for_model(Poll)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        council = Group.objects.get(name='Council')
        UserFactory.create(groups=['Council'])

        start = now() - timedelta(hours=3)
        poll = PollFactory.create(valid_groups=council,
                                  end=now() - timedelta(days=1),
                                  start=start)

        items = ActionItem.objects.filter(content_type=model)
        eq_(items.count(), 1)

        resolve_action_items()
        items = ActionItem.objects.filter(content_type=model, object_id=poll.id)
        for item in items:
            ok_(item.resolved)
            ok_(not item.completed)

    def test_update_valid_groups(self):
        model = ContentType.objects.get_for_model(Poll)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        council = Group.objects.get(name='Council')
        reps = Group.objects.get(name='Rep')
        UserFactory.create_batch(3, groups=['Council'])
        UserFactory.create_batch(4, groups=['Rep'])
        start = now() - timedelta(hours=3)
        poll = PollFactory.create(valid_groups=council, start=start)
        poll.valid_groups = reps
        poll.save()

        items = ActionItem.objects.filter(content_type=model, object_id=poll.id)
        eq_(items.count(), 4)

        for user in reps.user_set.all():
            ok_(items.filter(user=user).exists())

        for user in council.user_set.all():
            ok_(not items.filter(user=user).exists())

    def test_user_has_already_voted(self):
        model = ContentType.objects.get_for_model(Poll)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        council = Group.objects.get(name='Admin')
        user = UserFactory.create(groups=['Admin'])

        start = now() - timedelta(hours=3)
        poll = PollFactory.create(valid_groups=council,
                                  end=now() - timedelta(days=1),
                                  start=start)
        VoteFactory.create(poll=poll, user=user)

        # Check that there is only one action item and it's resolved
        items = ActionItem.objects.filter(content_type=model)
        eq_(items.count(), 1)
        eq_(items[0].resolved, True)


class EventActionItems(RemoTestCase):
    def setUp(self):
        ActivityFactory.create(name=ACTIVITY_EVENT_CREATE)
        ActivityFactory.create(name=ACTIVITY_EVENT_ATTEND)

    def test_post_event_metrics(self):
        model = ContentType.objects.get_for_model(Event)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        start = now() - timedelta(days=4)
        end = now() - timedelta(days=1)
        user = UserFactory.create(groups=['Rep'])
        event = EventFactory.create(owner=user, start=start, end=end)
        notify_event_owners_to_input_metrics()

        items = ActionItem.objects.filter(content_type=model, object_id=event.id)
        eq_(items.count(), 1)

    def test_resolve_post_event_metrics(self):
        model = ContentType.objects.get_for_model(Event)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        start = now() - timedelta(days=4)
        end = now() - timedelta(days=1)
        user = UserFactory.create(groups=['Rep'])
        event = EventFactory.create(owner=user, start=start, end=end)
        notify_event_owners_to_input_metrics()
        items = ActionItem.objects.filter(content_type=model, object_id=event.id)

        eq_(items.count(), 1)

        EventMetricOutcomeFactory.create(event=event)

        for item in items:
            ok_(item.completed)
            ok_(item.resolved)

    def test_update_event_owner(self):
        model = ContentType.objects.get_for_model(Event)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        start = now() - timedelta(days=4)
        end = now() - timedelta(days=1)
        user = UserFactory.create(groups=['Rep'])
        event = EventFactory.create(owner=user, start=start, end=end)
        notify_event_owners_to_input_metrics()

        items = ActionItem.objects.filter(content_type=model)
        eq_(items.count(), 1)

        new_owner = UserFactory.create(groups=['Rep'])
        event.owner = new_owner
        event.save()

        items = ActionItem.objects.filter(content_type=model, object_id=event.id)
        eq_(items.count(), 1)
        eq_(items[0].user, new_owner)


class ReportActionItems(RemoTestCase):
    def test_verify_activity(self):
        model = ContentType.objects.get_for_model(NGReport)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        activity = ActivityFactory.create(name=RECRUIT_MOZILLIAN)
        mentor = UserFactory.create()
        user = UserFactory.create(groups=['Rep'], userprofile__mentor=mentor)
        report = NGReportFactory.create(activity=activity, user=user,
                                        mentor=mentor)

        items = ActionItem.objects.filter(content_type=model,
                                          object_id=report.id,
                                          resolved=False)
        eq_(items.count(), 1)

    def test_resolve_verify_action_item(self):
        model = ContentType.objects.get_for_model(NGReport)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        activity = ActivityFactory.create(name=RECRUIT_MOZILLIAN)
        mentor = UserFactory.create()
        user = UserFactory.create(groups=['Rep'], userprofile__mentor=mentor)
        report = NGReportFactory.create(activity=activity, user=user,
                                        mentor=mentor)

        items = ActionItem.objects.filter(content_type=model,
                                          object_id=report.id,
                                          resolved=False)
        eq_(items.count(), 1)
        report.verified_activity = True
        report.save()

        for item in items:
            ok_(item.completed)
            ok_(item.resolved)


class ROTMActionItems(RemoTestCase):

    @mock.patch('remo.profiles.tasks.now')
    def test_base(self, mocked_date):
        model = ContentType.objects.get_for_model(UserProfile)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        mentors = UserFactory.create_batch(2, groups=['Mentor'])
        mocked_date.return_value = datetime(now().year, now().month, 1)
        send_rotm_nomination_reminder()

        items = ActionItem.objects.filter(content_type=model)

        eq_(items.count(), 2)
        eq_(set([mentor.id for mentor in mentors]),
            set(items.values_list('object_id', flat=True)))

    @mock.patch('remo.profiles.tasks.now')
    def test_invalid_date(self, mocked_date):
        model = ContentType.objects.get_for_model(UserProfile)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        UserFactory.create_batch(2, groups=['Mentor'])
        mocked_date.return_value = datetime(now().year, now().month, 2)
        send_rotm_nomination_reminder()

        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

    @mock.patch('remo.profiles.tasks.now')
    def test_resolve_action_item(self, mocked_date):
        model = ContentType.objects.get_for_model(UserProfile)
        user = UserFactory.create(groups=['Mentor'])
        mocked_date.return_value = datetime(now().year, now().month, 1)
        ActionItem.create(user.userprofile)
        items = ActionItem.objects.filter(content_type=model)
        eq_(items.count(), 1)
        eq_(items[0].resolved, False)

        mocked_date.return_value = datetime(now().year, now().month, 10)
        resolve_nomination_action_items()
        eq_(items.count(), 1)
        eq_(items[0].resolved, True)

    @mock.patch('remo.profiles.tasks.now')
    def test_resolve_action_item_invalid_date(self, mocked_date):
        model = ContentType.objects.get_for_model(UserProfile)
        user = UserFactory.create(groups=['Mentor'])
        mocked_date.return_value = datetime(now().year, now().month, 1)
        ActionItem.create(user.userprofile)
        items = ActionItem.objects.filter(content_type=model)
        eq_(items.count(), 1)
        eq_(items[0].resolved, False)

        mocked_date.return_value = datetime(now().year, now().month, 11)
        resolve_nomination_action_items()
        eq_(items.count(), 1)
        eq_(items[0].resolved, False)
