from datetime import datetime, timedelta
from operator import or_

from celery.task import periodic_task, task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.template.loader import render_to_string

from remo.base.tasks import send_remo_mail
from remo.base.utils import get_date
from remo.dashboard.models import ActionItem


EXTEND_VOTING_PERIOD = 24 * 3600  # 24 hours
NOTIFICATION_INTERVAL = 24 * 3600  # 24 hours


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
