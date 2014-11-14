from calendar import monthrange
from datetime import date, datetime, timedelta
from operator import or_

from celery.task import periodic_task, task
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils.timezone import now

from remo.base.tasks import send_remo_mail
from remo.base.utils import get_date, number2month
from remo.dashboard.models import ActionItem


EXTEND_VOTING_PERIOD = 24 * 3600  # 24 hours
NOTIFICATION_INTERVAL = 24 * 3600  # 24 hours
ROTM_NOMINATION_END_DATE = date(now().year, now().month, 10)


@task
def send_voting_mail(voting_id, subject, email_template):
    """Send to user_list emails based rendered using email_template
    and populated with data.

    """
    # avoid circular dependencies
    from remo.voting.models import Poll

    poll = Poll.objects.get(pk=voting_id)
    data = {'SITE_URL': settings.SITE_URL,
            'FROM_EMAIL': settings.FROM_EMAIL,
            'poll': poll}

    if poll.automated_poll:
        message = render_to_string(email_template, data)
        send_mail(subject, message, settings.FROM_EMAIL,
                  [settings.REPS_COUNCIL_ALIAS])
    else:
        user_list = User.objects.filter(groups=poll.valid_groups)

        for user in user_list:
            ctx_data = {'user': user,
                        'userprofile': user.userprofile}
            ctx_data.update(data)
            message = render_to_string(email_template, ctx_data)
            send_mail(subject, message, settings.FROM_EMAIL, [user.email])


@periodic_task(run_every=timedelta(hours=8))
def extend_voting_period():
    """Extend voting period by EXTEND_VOTING_PERIOD if there is no
    majority decision.

    """

    # avoid circular dependencies
    from remo.voting.models import Poll

    tomorrow = get_date(days=1)
    council_count = User.objects.filter(groups__name='Council').count()

    polls = Poll.objects.filter(end__year=tomorrow.year,
                                end__month=tomorrow.month,
                                end__day=tomorrow.day,
                                automated_poll=True)

    for poll in polls:
        if not poll.is_extended:
            budget_poll = poll.radio_polls.get(question='Budget Approval')
            majority = reduce(or_, map(lambda x: x.votes > council_count/2,
                                       budget_poll.answers.all()))
            if not majority:
                poll.end += timedelta(seconds=EXTEND_VOTING_PERIOD)
                poll.save()
                subject = '[Urgent] Voting extended for {0}'.format(poll.name)
                recipients = (User.objects.filter(groups=poll.valid_groups)
                              .exclude(pk__in=poll.users_voted.all())
                              .values_list('id', flat=True))
                ctx_data = {'poll': poll}
                template = 'emails/voting_vote_reminder.txt'
                send_remo_mail.delay(subject=subject,
                                     recipients_list=recipients,
                                     email_template=template,
                                     data=ctx_data)


@periodic_task(run_every=timedelta(days=1))
def resolve_action_items():
    # avoid circular dependencies
    from remo.voting.models import Poll

    start = datetime.combine(get_date(days=-1), datetime.min.time())
    end = datetime.combine(get_date(days=-1), datetime.max.time())
    polls = Poll.objects.filter(end__range=[start, end])
    action_model = ContentType.objects.get_for_model(Poll)
    items = ActionItem.objects.filter(content_type=action_model,
                                      object_id__in=polls)
    items.update(resolved=True)


@periodic_task(run_every=timedelta(hours=4))
def create_poll_action_items():
    """Create action items for current polls."""
    # avoid circular dependencies
    from remo.voting.models import Poll

    start = now() - timedelta(hours=4)
    polls = Poll.objects.filter(start__range=[start, now()])
    for poll in polls:
        ActionItem.create(poll)


@periodic_task(run_every=timedelta(hours=24))
def create_rotm_poll():
    """Create a poll for the Rep of the month nominee.

    This task will create a range poll after the first days of the month
    during which mentors nominated mentees through their user profiles.
    The poll will end 5 days before the end of each month.
    """
    # Avoid circular dependencies
    from remo.voting.models import Poll, RangePoll, RangePollChoice

    poll_name = 'Rep of the month for {0}'.format(number2month(now().month))
    days_of_month = monthrange(now().year, now().month)[1]
    start = datetime.combine(date(now().year, now().month, 1),
                             datetime.min.time())
    end = datetime.combine(date(now().year, now().month, days_of_month),
                           datetime.max.time())
    end -= timedelta(days=5)
    rotm_poll = Poll.objects.filter(name=poll_name,
                                    start__range=[start, end],
                                    end__range=[start, end])

    if not now().date() > ROTM_NOMINATION_END_DATE or rotm_poll.exists():
        return

    remobot = User.objects.get(username='remobot')
    description = 'Automated vote for the Rep of this month.'
    mentor_group = Group.objects.get(name='Mentor')
    nominees = User.objects.filter(userprofile__registration_complete=True,
                                   userprofile__is_rotm_nominee=True)

    with transaction.commit_on_success():
        poll = Poll.objects.create(name=poll_name,
                                   description=description,
                                   valid_groups=mentor_group,
                                   start=now() + timedelta(hours=8),
                                   end=end,
                                   created_by=remobot)
        range_poll = RangePoll.objects.create(poll=poll,
                                              name='Rep of the month nominees')
        for nominee in nominees:
            RangePollChoice.objects.create(range_poll=range_poll,
                                           nominee=nominee)
