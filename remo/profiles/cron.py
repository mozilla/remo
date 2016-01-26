from django.conf import settings
from django.utils.timezone import now

from cronjobs import register

from remo.profiles.models import UserProfile
from remo.profiles.tasks import send_generic_mail
from remo.base.utils import go_back_n_months


@register
def new_reps_reminder():
    """Send email to reps-mentors listing new subscribers the past month."""

    prev = go_back_n_months(now().date())
    prev_date = prev.strftime('%B %Y')

    reps = UserProfile.objects
    reps_num = reps.count()
    new_reps = reps.filter(date_joined_program__month=prev.month)
    email_template = 'emails/new_reps_monthly_reminder.jinja'
    subject = '[Info] New Reps for %s' % prev_date
    recipient = settings.REPS_MENTORS_LIST
    data = {'reps': new_reps, 'date': prev_date, 'reps_num': reps_num}

    send_generic_mail.delay([recipient], subject, email_template, data)
