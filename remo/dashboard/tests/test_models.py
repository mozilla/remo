from django.contrib.contenttypes.models import ContentType
from nose.tools import eq_, ok_

from remo.base.tests import RemoTestCase
from remo.dashboard.models import ActionItem
from remo.profiles.tests import UserFactory
from remo.remozilla.models import Bug
from remo.remozilla.tests import BugFactory


class CreateActionItemWhiteboard(RemoTestCase):
    """Test related to new action items created from bugzilla."""

    def test_waiting_receipts(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type__pk=model.id)
        ok_(not items.exists())

        whiteboard = '[waiting receipts]'
        user = UserFactory.create(groups=['Rep'])
        BugFactory.create(whiteboard=whiteboard, assigned_to=user)

        items = ActionItem.objects.filter(content_type__pk=model.id)
        eq_(items.count(), 1)
        eq_(items[0].action_type, 'Add receipts to bug')
        eq_(items[0].user, user)
        eq_(items[0].priority, 2)

    def test_waiting_multiple_proofs(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type__pk=model.id)
        ok_(not items.exists())

        whiteboard = '[waiting receipts][waiting report][waiting photos]'
        user = user = UserFactory.create(groups=['Rep'])
        BugFactory.create(whiteboard=whiteboard, assigned_to=user)

        items = ActionItem.objects.filter(content_type__pk=model.id)
        eq_(items.count(), 3)

    def test_mentor_validation(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type__pk=model.id)

        ok_(not items.exists())

        mentor = UserFactory.create(groups=['Rep', 'Mentor'])
        user = UserFactory.create(groups=['Rep', 'Mentor'],
                                  userprofile__mentor=mentor)

        BugFactory.create(pending_mentor_validation=True, assigned_to=user)

        items = ActionItem.objects.filter(content_type__pk=model.id)
        eq_(items.count(), 1)
        eq_(items[0].action_type, 'Review budget request bug')
        eq_(items[0].user, mentor)
        eq_(items[0].priority, 5)


class SyncActionItemNeedinfo(RemoTestCase):

    def test_needinfo(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type__pk=model.id)

        ok_(not items.exists())

        users = UserFactory.create_batch(5, groups=['Rep'])
        bug = BugFactory.create()
        bug.budget_needinfo.add(*users)
        bug.save()

        items = ActionItem.objects.filter(content_type__pk=model.id)
        ok_(items.count(), 5)

        for item in items:
            eq_(item.action_type, 'Pending open questions')
            ok_(item.user in users)
            ok_(item.priority, 1)


class SyncActionItemCouncilReviewer(RemoTestCase):
    def test_council_reviewer_assigned(self):
        model = ContentType.objects.get_for_model(Bug)
        items = ActionItem.objects.filter(content_type__pk=model.id)
        ok_(not items.exists())

        user = UserFactory.create(groups=['Council'])
        BugFactory.create(assigned_to=user, council_member_assigned=True)

        items = ActionItem.objects.filter(content_type__pk=model.id)
        eq_(items.count(), 1)
        eq_(items[0].action_type, 'Council reviewer assigned')
        eq_(items[0].user, user)
        eq_(items[0].priority, 5)
