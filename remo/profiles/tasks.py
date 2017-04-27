from calendar import monthrange
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.timezone import now

import waffle
from celery.task import periodic_task, task

from remo.base.mozillians import BadStatusCode, MozilliansClient, ResourceDoesNotExist
from remo.base.tasks import send_remo_mail
from remo.base.utils import get_date, number2month
from remo.dashboard.models import ActionItem
from remo.profiles.models import (UserProfile, UserStatus,
                                  NOMINATION_ACTION_ITEM)


ROTM_REMINDER_DAY = 1
NOMINATION_END_DAY = 10


@task
def send_generic_mail(recipient_list, subject, email_template, data={}):
    """Send email to recipient_list rendered using email_template and populated
    with data.
    """
    data.update({'SITE_URL': settings.SITE_URL,
                 'FROM_EMAIL': settings.FROM_EMAIL})

    message = render_to_string(email_template, data)
    send_mail(subject, message, settings.FROM_EMAIL, recipient_list)


@periodic_task(run_every=timedelta(hours=24), soft_time_limit=600)
def check_mozillian_username():
    mozillians = User.objects.filter(groups__name='Mozillians')
    client = MozilliansClient(settings.MOZILLIANS_API_URL,
                              settings.MOZILLIANS_API_KEY)

    for user in mozillians:
        try:
            data = client.lookup_user({'email': user.email})
        except (BadStatusCode, ResourceDoesNotExist):
            data = None

        if data and data['is_vouched'] and data['full_name']['privacy'] == 'Public':
            full_name = data['full_name']['value']
            first_name, last_name = (full_name.split(' ', 1)
                                     if ' ' in full_name else ('', full_name))
            user.first_name = first_name
            user.last_name = last_name
            user.userprofile.mozillian_username = data['username']
        else:
            user.first_name = 'Anonymous'
            user.last_name = 'Mozillian'
            user.userprofile.mozillian_username = ''
        if len(user.last_name) > 30:
            user.last_name = user.last_name[:30]
        if len(user.first_name) > 30:
            user.first_name = user.first_name[:30]
        user.save()
        user.userprofile.save()


@task(ignore_result=False)
def check_celery():
    """Dummy celery task to check that everything runs smoothly."""
    pass


@periodic_task(run_every=timedelta(hours=24))
def reset_rotm_nominees():
    """Reset the Rep of the month nomination in user profiles.

    This task will reset the nomination bit for the Rep of the month in the
    user profiles, for all the users nominated in each month. This will take
    place at the last day of each month.
    """

    now_date = now().date()
    days_of_month = monthrange(now_date.year, now_date.month)[1]
    if (now_date == date(now_date.year, now_date.month, days_of_month) or
            waffle.switch_is_active('enable_rotm_tasks')):
        nominees = UserProfile.objects.filter(is_rotm_nominee=True)
        for nominee in nominees:
            nominee.is_rotm_nominee = False
            nominee.rotm_nominated_by = None
            nominee.save()


@periodic_task(run_every=timedelta(hours=24))
def send_rotm_nomination_reminder():
    """ Send an email reminder to all mentors.

    The first day of each month, the mentor group receives an email reminder
    in order to nominate Reps for the Rep of the month voting.
    """

    now_date = now().date()
    if (now_date.day == ROTM_REMINDER_DAY or
            waffle.switch_is_active('enable_rotm_tasks')):
        data = {'month': number2month(now_date.month)}
        subject = 'Nominate Rep of the month'
        template = 'emails/mentors_rotm_reminder.jinja'
        send_remo_mail(subject=subject,
                       email_template=template,
                       recipients_list=[settings.REPS_MENTORS_LIST],
                       data=data)
        mentors = User.objects.filter(groups__name='Mentor')
        for mentor in mentors:
            ActionItem.create(mentor.userprofile)


@periodic_task(run_every=timedelta(hours=12))
def set_unavailability_flag():
    """Set the unavailable flag in UserStatus.

    This task runs every 12 hours and sets the unavailable flag to True
    in the case that a user has submitted a 'break notification' with a start
    date in the future."""

    (UserStatus.objects.filter(start_date__range=[get_date(-1), get_date()],
                               is_unavailable=False)
                       .update(is_unavailable=True))


@periodic_task(run_every=timedelta(hours=24))
def resolve_nomination_action_items():
    """Resolve action items.

    Resolve all the action items relevant to nomination reminders after the
    10th day of each month.
    """

    today = now().date()
    if (today.day == NOMINATION_END_DAY or
            waffle.switch_is_active('enable_rotm_tasks')):
        mentors = UserProfile.objects.filter(user__groups__name='Mentor')
        action_model = ContentType.objects.get_for_model(UserProfile)
        # All the completed action items are always resolved
        name = u'{0} {1}'.format(NOMINATION_ACTION_ITEM, today.strftime('%B'))
        items = (ActionItem.objects.filter(content_type=action_model,
                                           object_id__in=mentors,
                                           name=name)
                                   .exclude(completed=True))
        items.update(resolved=True)
