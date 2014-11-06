from datetime import timedelta

from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now

from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.dashboard.models import ActionItem
from remo.events.models import Event
from remo.events.tasks import notify_event_owners_to_input_metrics
from remo.events.tests import EventFactory, EventMetricOutcomeFactory
from remo.profiles.tests import UserFactory
from remo.remozilla.models import Bug
from remo.remozilla.tests import BugFactory
from remo.voting.models import Poll
from remo.voting.tasks import resolve_action_items, create_poll_action_items
from remo.voting.tests import PollFactory, VoteFactory


class RemozillaActionItems(RemoTestCase):
    """Test related to new action items created from bugzilla."""

    def test_waiting_receipts(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        whiteboard = '[waiting receipts]'
        user = UserFactory.create(groups=['Rep'])
        bug = BugFactory.build(whiteboard=whiteboard, assigned_to=user)
        bug.save()

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
        bug = BugFactory.build(whiteboard=whiteboard, assigned_to=user)
        bug.save()

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
        bug = BugFactory.build(whiteboard=whiteboard, assigned_to=user)
        bug.save()

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

        bug = BugFactory.build(pending_mentor_validation=True,
                               assigned_to=mentor)
        bug.save()

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
        bug = BugFactory.build(assigned_to=user_1,
                               pending_mentor_validation=True)
        bug.save()
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

        bug = BugFactory.build(pending_mentor_validation=True,
                               assigned_to=mentor)
        bug.save()

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
        bug = BugFactory.build(assigned_to=user)
        bug.save()
        bug.budget_needinfo.add(needinfo)
        bug.save()

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
        bug.save()

        bug.budget_needinfo.clear()
        bug.save()

        items = ActionItem.objects.filter(content_type=model, object_id=bug.id)
        for item in items:
            ok_(item.completed)
            ok_(item.resolved)

    def test_council_reviewer_assigned(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        user = UserFactory.create(groups=['Rep', 'Council'])
        bug = BugFactory.build(assigned_to=user, council_member_assigned=True)
        bug.save()

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
        bug = BugFactory.build(assigned_to=user,
                               council_member_assigned=True)
        bug.save()

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
        bug = BugFactory.build(pending_mentor_validation=True,
                               assigned_to=user)
        bug.save()

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

        create_poll_action_items()

        items = ActionItem.objects.filter(content_type=model,
                                          object_id=poll.id)
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
        poll = PollFactory.create(valid_groups=council, automated_poll=True,
                                  bug=bug, start=start)

        create_poll_action_items()

        items = ActionItem.objects.filter(content_type=model,
                                          object_id=poll.id)
        eq_(items.count(), 1)

        for item in items:
            eq_(item.name,
                'Cast your vote for budget request ' + poll.bug.summary)
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

        create_poll_action_items()

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

        create_poll_action_items()

        VoteFactory.create(poll=poll, user=user)

        items = ActionItem.objects.filter(content_type=model,
                                          object_id=poll.id)
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

        create_poll_action_items()

        poll.end = poll.end + timedelta(days=4)
        poll.save()

        items = ActionItem.objects.filter(content_type=model,
                                          object_id=poll.id)
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

        create_poll_action_items()

        items = ActionItem.objects.filter(content_type=model)
        eq_(items.count(), 1)

        resolve_action_items()
        items = ActionItem.objects.filter(content_type=model,
                                          object_id=poll.id)
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

        create_poll_action_items()

        poll.valid_groups = reps
        poll.save()

        items = ActionItem.objects.filter(content_type=model,
                                          object_id=poll.id)
        eq_(items.count(), 4)

        for user in reps.user_set.all():
            ok_(items.filter(user=user).exists())

        for user in council.user_set.all():
            ok_(not items.filter(user=user).exists())


class EventActionItems(RemoTestCase):
    def test_post_event_metrics(self):
        model = ContentType.objects.get_for_model(Event)
        items = ActionItem.objects.filter(content_type=model)
        ok_(not items.exists())

        start = now() - timedelta(days=4)
        end = now() - timedelta(days=1)
        user = UserFactory.create(groups=['Rep'])
        event = EventFactory.create(owner=user, start=start, end=end)
        notify_event_owners_to_input_metrics()

        items = ActionItem.objects.filter(content_type=model,
                                          object_id=event.id)
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
        items = ActionItem.objects.filter(content_type=model,
                                          object_id=event.id)

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

        items = ActionItem.objects.filter(content_type=model,
                                          object_id=event.id)
        eq_(items.count(), 1)
        eq_(items[0].user, new_owner)
