from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.contrib.auth.models import User
from django.dispatch import receiver

from remo.base.tasks import send_remo_mail
from remo.base.utils import daterange, get_date
from remo.events.models import Attendance as EventAttendance, Event
from remo.profiles.models import FunctionalArea
from remo.reports import ACTIVITY_EVENT_ATTEND, ACTIVITY_EVENT_CREATE, ACTIVITY_POST_EVENT_METRICS
from remo.reports.models import Activity, NGReport, NGReportComment


@receiver(post_save, sender=EventAttendance,
          dispatch_uid='create_passive_attendance_report_signal')
def create_passive_attendance_report(sender, instance, **kwargs):
    """Automatically create a passive report after event attendance save."""
    from remo.events.templatetags.helpers import get_event_link

    if instance.user.groups.filter(name='Rep').exists():
        activity = Activity.objects.get(name=ACTIVITY_EVENT_ATTEND)
        attrs = {
            'user': instance.user,
            'event': instance.event,
            'activity': activity,
            'report_date': instance.event.start.date(),
            'longitude': instance.event.lon,
            'latitude': instance.event.lat,
            'location': "%s, %s, %s" % (instance.event.city,
                                        instance.event.region,
                                        instance.event.country),
            'is_passive': True,
            'country': instance.event.country,
            'link': get_event_link(instance.event),
            'activity_description': instance.event.description}

        report = NGReport.objects.create(**attrs)
        report.functional_areas.add(*instance.event.categories.all())


@receiver(post_save, sender=Event,
          dispatch_uid='create_update_passive_event_creation_report_signal')
def create_update_passive_event_report(sender, instance, created, **kwargs):
    """Automatically create/update a passive report on event creation."""
    from remo.events.templatetags.helpers import get_event_link

    attrs = {
        'report_date': instance.start.date(),
        'longitude': instance.lon,
        'latitude': instance.lat,
        'location': "%s, %s, %s" % (instance.city,
                                    instance.region,
                                    instance.country),
        'link': get_event_link(instance),
        'activity_description': instance.description,
        'is_passive': True,
        'event': instance,
        'campaign': instance.campaign,
        'country': instance.country
    }

    if created:
        activity = Activity.objects.get(name=ACTIVITY_EVENT_CREATE)
        attrs.update({'user': instance.owner,
                      'activity': activity})

        NGReport.objects.create(**attrs)
    else:
        reports = (NGReport.objects.filter(event=instance)
                   .exclude(activity__name=ACTIVITY_POST_EVENT_METRICS))
        reports.update(**attrs)
        # Change user and mentor to the appropriate reports
        attrs.update({'user': instance.owner,
                      'mentor': instance.owner.userprofile.mentor})
        reports.exclude(activity__name=ACTIVITY_EVENT_ATTEND).update(**attrs)


@receiver(pre_delete, sender=EventAttendance,
          dispatch_uid='delete_passive_report_attendance_signal')
def delete_passive_attendance_report(sender, instance, **kwargs):
    """Automatically delete a passive report after event attendance delete."""
    attrs = {
        'user': instance.user,
        'event': instance.event,
        'activity': Activity.objects.get(name=ACTIVITY_EVENT_ATTEND)}

    NGReport.objects.filter(**attrs).delete()


@receiver(pre_delete, sender=Event, dispatch_uid='delete_passive_report_event_signal')
def delete_passive_event_report(sender, instance, **kwargs):
    """Automatically delete a passive report after an event is deleted."""
    NGReport.objects.filter(event=instance).delete()


@receiver(m2m_changed, sender=Event.categories.through,
          dispatch_uid='update_passive_report_categories_signal')
def update_passive_report_functional_areas(sender, instance, action, pk_set,
                                           **kwargs):
    """Automatically update passive report's functional areas."""
    reports = NGReport.objects.filter(event=instance)

    for report in reports:
        if action == 'post_add':
            for pk in pk_set:
                obj = FunctionalArea.objects.get(id=pk)
                report.functional_areas.add(obj)

        if action == 'post_remove':
            for pk in pk_set:
                obj = FunctionalArea.objects.get(id=pk)
                report.functional_areas.remove(obj)

        if action == 'post_clear':
            report.functional_areas.clear()


@receiver(post_save, sender=NGReportComment,
          dispatch_uid='email_commenters_on_add_ng_report_comment_signal')
def email_commenters_on_add_ng_report_comment(sender, instance, **kwargs):
    """Email a user when a comment is added to a continuous report instance."""
    subject = '[Report] User {0} commented on {1}'
    email_template = 'emails/user_notification_on_add_ng_report_comment.jinja'
    report = instance.report

    # Send an email to all users commented so far on the report except fom
    # the user who made the comment. Dedup the list with unique IDs.
    commenters = set(NGReportComment.objects.filter(report=report)
                     .exclude(user=instance.user)
                     .values_list('user', flat=True))

    # Add the owner of the report in the list
    if report.user.id not in commenters:
        commenters.add(report.user.id)

    for user_id in commenters:
        user = User.objects.get(pk=user_id)
        if user.userprofile.receive_email_on_add_comment and user != instance.user:
            ctx_data = {'report': report, 'user': user,
                        'commenter': instance.user,
                        'comment': instance.comment,
                        'created_on': instance.created_on}
            subject = subject.format(instance.user.get_full_name(), report)
            send_remo_mail.delay(subject=subject, recipients_list=[user_id],
                                 email_template=email_template, data=ctx_data)


@receiver(pre_delete, sender=NGReport, dispatch_uid='delete_ng_report_signal')
def delete_ng_report(sender, instance, **kwargs):
    """Automatically update user's streak counters."""
    today = get_date()
    current_start = instance.user.userprofile.current_streak_start or None
    longest_start = instance.user.userprofile.longest_streak_start or None
    longest_end = instance.user.userprofile.longest_streak_end or None

    # If instance is in the future or there is another
    # report that date, don't do anything
    if (instance.is_future_report or
            (NGReport.objects.filter(user=instance.user, report_date=instance.report_date)
                             .exclude(pk=instance.id).exists())):
        return

    try:
        next_report = instance.get_next_by_report_date(user=instance.user, report_date__lte=today)
    except NGReport.DoesNotExist:
        next_report = None

    try:
        previous_report = instance.get_previous_by_report_date(user=instance.user)
    except NGReport.DoesNotExist:
        previous_report = None

    # There aren't any reports
    if not next_report and not previous_report:
        current_start = None
        longest_start = None
        longest_end = None

    # If the deleted report is between the range of the longest
    # streak counters, we need to update them.
    elif (longest_start and longest_end and
            instance.report_date in daterange(longest_start, longest_end)):

        if longest_start == instance.report_date and next_report:
            longest_start = next_report.report_date
        elif longest_end == instance.report_date and previous_report:
            longest_end = previous_report.report_date
        elif (previous_report and next_report and
              (next_report.report_date -
               previous_report.report_date).days > 7):
            # Compare the number of reports registered from the starting point
            # of the longest streak up until the date of the deleted report,
            # with the number of reports registered from the date of the
            # deleted report until the end of the longest streak.
            lower_half_report_count = NGReport.objects.filter(
                report_date__range=(longest_start, instance.report_date),
                user=instance.user).count()
            upper_half_report_count = NGReport.objects.filter(
                report_date__range=(instance.report_date, longest_end),
                user=instance.user).count()

            # If the first time slice contains more reports, then we need
            # to move the end of the longest streak, just before
            # the deletion point. If the opposite is true, move the starting
            # point of the longest streak just after the deletion point.
            if (lower_half_report_count >= upper_half_report_count and
                    previous_report.report_date >= longest_start):
                longest_end = previous_report.report_date
            elif (upper_half_report_count > lower_half_report_count and
                    next_report.report_date <= longest_end):
                longest_start = next_report.report_date

    # If the deleted report is between the range of the current
    # streak counter and today, then we need to update the counter.
    if current_start and instance.report_date in daterange(current_start, today):
        if current_start == instance.report_date and next_report:
            current_start = next_report.report_date
        elif (previous_report and next_report and
                (next_report.report_date -
                 previous_report.report_date).days > 7):
            current_start = next_report.report_date

    instance.user.userprofile.current_streak_start = current_start
    instance.user.userprofile.longest_streak_start = longest_start
    instance.user.userprofile.longest_streak_end = longest_end
    instance.user.userprofile.save()
