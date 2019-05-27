from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.db.models import Q, Count
from django.shortcuts import redirect, render
from django.utils.timezone import now
from django.views.decorators.cache import never_cache

from django_statsd.clients import statsd
from product_details import product_details

import forms
from remo.base.decorators import permission_check
from remo.base.forms import EmailUsersForm
from remo.base.utils import get_date
from remo.dashboard.models import ActionItem
from remo.events.models import Event
from remo.profiles.models import UserStatus, FunctionalArea
from remo.remozilla.models import Bug
from remo.reports.models import NGReport, Campaign


# Action Items
LIST_ACTION_ITEMS_DEFAULT_SORT = 'action_item_date_desc'
LIST_ACTION_ITEMS_VALID_SORTS = {
    'action_desc': '-name',
    'action_asc': 'name',
    'action_item_priority_desc': '-priority',
    'action_item_priority_asc': 'priority',
    'action_item_date_desc': '-due_date',
    'action_item_date_asc': 'due_date'
}


def dashboard_mozillians(request, user):
    args = {}
    user_profile = user.userprofile
    interestform = forms.TrackFunctionalAreasForm(request.POST or None, instance=user_profile)
    reps_email_form = forms.EmailRepsForm(request.POST or None)
    if interestform.is_valid():
        interestform.save()
        messages.success(request, 'Interests successfully saved')
        return redirect('dashboard')
    if reps_email_form.is_valid():
        functional_area = reps_email_form.cleaned_data['functional_area']
        reps = User.objects.filter(groups__name='Rep').filter(
            userprofile__functional_areas=functional_area)
        reps_email_form.send_email(request, reps)
        return redirect('dashboard')

    # Get the reps who match the specified interests
    interests = user.userprofile.tracked_functional_areas.all()
    tracked_interests = {}
    reps_past_events = {}
    reps_current_events = {}
    reps_ng_reports = {}
    today = now().date()
    unavailable_rep_exists = {}

    for interest in interests:
        # Get the Reps with the specified interest
        reps = User.objects.filter(groups__name='Rep').filter(
            userprofile__functional_areas=interest)
        tracked_interests[interest.name] = {
            'id': interest.id,
            'reps': reps
        }

        # Get the reports of the Reps with the specified interest
        ng_reports = NGReport.objects.filter(report_date__lte=today,
                                             functional_areas=interest,
                                             user__in=reps)
        reps_ng_reports[interest.name] = ng_reports.order_by('-report_date')[:10]

        # Get the events with the specified category
        events = Event.objects.filter(categories=interest)
        reps_past_events[interest.name] = events.filter(start__lt=now())[:50]
        reps_current_events[interest.name] = events.filter(start__gte=now())

        # Check if there is an unavailable Rep for the specific interest
        unavailable_val = (UserStatus.objects.filter(is_unavailable=True)
                                             .filter(user__in=reps).exists())
        unavailable_rep_exists[interest.name] = unavailable_val

    args['unavailable_rep_exists'] = unavailable_rep_exists
    args['reps_ng_reports'] = reps_ng_reports
    args['interestform'] = interestform
    args['reps_past_events'] = reps_past_events
    args['reps_current_events'] = reps_current_events
    args['tracked_interests'] = tracked_interests
    args['reps_email_form'] = reps_email_form
    statsd.incr('dashboard.dashboard_mozillians')
    return render(request, 'dashboard_mozillians.jinja', args)


@never_cache
@permission_check()
def dashboard(request):
    """Dashboard view."""
    user = request.user
    args = {'today': now()}

    # Mozillians/Alumni block
    if (user.groups.filter(name='Mozillians').exists()
            or user.groups.filter(name='Alumni').exists()):
        return dashboard_mozillians(request, user)

    # Reps block
    q_closed = Q(status='RESOLVED') | Q(status='VERIFIED')
    budget_requests = Bug.objects.filter(component='Budget Requests').exclude(q_closed)
    swag_requests = Bug.objects.filter(component='Swag Requests').exclude(q_closed)
    mentorship_requests = Bug.objects.filter(component='Mentorship').exclude(q_closed)

    today = now().date()

    # Action Items
    args['action_items'] = ActionItem.objects.filter(user=user, resolved=False)[:10]

    # NG Reports
    if user.groups.filter(name='Rep').exists():
        args['ng_reports'] = user.ng_reports.filter(
            report_date__lte=today).order_by('-report_date')

    # Dashboard data
    my_q = (Q(cc=user) | Q(creator=user))
    my_q_assigned = (my_q | Q(assigned_to=user))
    my_mentees = User.objects.filter(userprofile__mentor=user,
                                     userprofile__registration_complete=True,
                                     groups__name='Rep')
    reps = User.objects.filter(groups__name='Rep')

    args['my_budget_requests'] = budget_requests.filter(my_q).distinct()
    args['my_swag_requests'] = swag_requests.filter(my_q).distinct()

    if user.groups.filter(
        Q(name='Admin')
        | Q(name='Council')
        | Q(name='Peers')
        | Q(name='Onboarding')
    ).exists():
        args['can_view_administration'] = True

    if user.groups.filter(name='Mentor').exists():
        args['mentees_action_items'] = ActionItem.objects.filter(user__in=my_mentees,
                                                                 resolved=False)[:10]
        args['mentees_activities'] = User.objects.filter(
            userprofile__registration_complete=True,
            userprofile__mentor=user,
            groups__name='Rep').distinct()
        args['mentees_budget_requests'] = budget_requests.filter(creator__in=my_mentees).distinct()
        args['mentees_swag_requests'] = swag_requests.filter(creator__in=my_mentees).distinct()
        args['mentees_emails'] = my_mentees.values_list('first_name', 'last_name', 'email') or None
        args['email_mentees_form'] = EmailUsersForm(my_mentees)

    if user.groups.filter(Q(name='Mentor') | Q(name='Council')).exists():
        my_mentorship_requests = mentorship_requests.filter(my_q_assigned)
        my_mentorship_requests = my_mentorship_requests.order_by('whiteboard')
        args['my_mentorship_requests'] = my_mentorship_requests.distinct()

    if user.groups.filter(Q(name='Admin') | Q(name='Review')).exists():
        args['all_budget_requests'] = budget_requests.all()[:20]
        args['all_swag_requests'] = swag_requests.all()[:20]

    if user.groups.filter(Q(name='Admin') | Q(name='Council') | Q(name='Onboarding')).exists():
        args['reps_without_profile'] = reps.filter(userprofile__registration_complete=False)

    if user.groups.filter(Q(name='Admin') | Q(name='Council') | Q(name='Peers')).exists():
        # We want to show
        #   - Reps with completed profiles and no mentor
        #   - Reps with mentors who are Alumni
        # while not including any Alumni Reps
        alumni_ids = User.objects.filter(groups__name='Alumni').values_list('id', flat=True)
        reps_with_alumni_mentors_q = Q(userprofile__mentor__id__in=alumni_ids)
        reps_without_mentor_q = Q(userprofile__registration_complete=True,
                                  userprofile__mentor__isnull=True)
        reps_without_mentor = reps.filter(reps_with_alumni_mentors_q
                                          | reps_without_mentor_q)
        order_by = '-userprofile__date_joined_program'
        args['reps_without_mentors'] = reps_without_mentor.order_by(order_by)

        reps_with_profiles = reps.filter(userprofile__registration_complete=True)
        q_active_12_months = Q(
            ng_reports__report_date__range=[get_date(weeks=-52), get_date(weeks=0)])
        args['reps_inactive_12_months'] = reps_with_profiles.filter(~q_active_12_months).distinct()
        q_active_6_months = Q(
            ng_reports__report_date__range=[get_date(weeks=-26), get_date(weeks=0)])
        args['reps_inactive_6_months'] = reps_with_profiles.filter(~q_active_6_months).distinct()

    statsd.incr('dashboard.dashboard_reps')
    return render(request, 'dashboard_reps.jinja', args)


@permission_check(group='Mentor')
def email_mentees(request):
    """Email my mentees view."""
    if request.method == 'POST':
        my_mentees = User.objects.filter(userprofile__mentor=request.user)
        email_form = EmailUsersForm(my_mentees, request.POST)
        if email_form.is_valid():
            email_form.send_mail(request)
        else:
            messages.error(request, 'Email not sent. Invalid data.')

    return redirect('dashboard')


def stats_dashboard(request):
    """Stats dashboard view."""
    reps = User.objects.filter(groups__name='Rep',
                               userprofile__registration_complete=True)

    q_active = Q(
        ng_reports__report_date__range=[get_date(weeks=-4), get_date(weeks=4)])
    q_inactive = Q(
        ng_reports__report_date__range=[get_date(weeks=-8), get_date(weeks=8)])

    q_active_month1 = Q(
        ng_reports__report_date__range=[get_date(weeks=-4), get_date(weeks=0)])
    q_active_month2 = Q(
        ng_reports__report_date__range=[get_date(weeks=-8), get_date(weeks=0)])
    q_active_month6 = Q(
        ng_reports__report_date__range=[get_date(weeks=-26), get_date(weeks=0)])
    q_active_month12 = Q(
        ng_reports__report_date__range=[get_date(weeks=-52), get_date(weeks=0)])

    top_countries = (User.objects
                     .values('userprofile__country')
                     .annotate(country_count=Count('userprofile__country'))
                     .order_by('-country_count')[:10])

    active = reps.filter(q_active)
    active_month1 = reps.filter(q_active_month1)
    active_month2 = reps.filter(q_active_month2)
    active_month6 = reps.filter(q_active_month6)
    active_month12 = reps.filter(q_active_month12)
    inactive_low = reps.filter(~q_active & q_inactive)
    inactive_high = reps.filter(~q_inactive)

    args = {}
    args['active_users'] = active.distinct().count()
    args['inactive_low_users'] = inactive_low.distinct().count()
    args['inactive_high_users'] = inactive_high.distinct().count()
    args['reps'] = reps.count()
    args['past_events'] = Event.objects.filter(start__lt=now()).count()
    args['future_events'] = Event.objects.filter(start__gte=now()).count()
    args['activities'] = NGReport.objects.all().count()
    args['active_month1'] = active_month1.distinct().count()
    args['active_month2'] = active_month2.distinct().count()
    args['active_month6'] = active_month6.distinct().count()
    args['active_month12'] = active_month12.distinct().count()
    args['top_countries'] = top_countries

    return render(request, 'stats_dashboard.jinja', args)


@never_cache
@permission_check()
def list_action_items(request):
    user = request.user
    action_items = ActionItem.objects.filter(user=user,
                                             resolved=False)
    pageheader = 'My Action Items'

    if 'query' in request.GET:
        query = request.GET['query'].strip()
        reversed_priority = dict((v.lower(), k) for k, v in ActionItem.PRIORITY_CHOICES)
        priority = reversed_priority.get(query.lower(), '')
        if priority:
            action_items = action_items.filter(Q(priority=priority))
        else:
            action_items = action_items.filter(Q(name__icontains=query))

    action_items = action_items.distinct()
    number_of_action_items = action_items.count()

    sort_key = request.GET.get('sort_key', LIST_ACTION_ITEMS_DEFAULT_SORT)
    if sort_key not in LIST_ACTION_ITEMS_VALID_SORTS:
        sort_key = LIST_ACTION_ITEMS_DEFAULT_SORT

    sort_by = LIST_ACTION_ITEMS_VALID_SORTS[sort_key]
    action_items = action_items.order_by(*sort_by.split(','))

    paginator = Paginator(action_items, settings.ITEMS_PER_PAGE)

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        actions = paginator.page(page)
    except (EmptyPage, InvalidPage):
        actions = paginator.page(paginator.num_pages)

    return render(request, 'list_action_items.jinja',
                  {'objects': actions,
                   'number_of_action_items': number_of_action_items,
                   'sort_key': sort_key,
                   'pageheader': pageheader,
                   'pageuser': user,
                   'query': request.GET.get('query', '')})


def kpi(request):
    countries = product_details.get_regions('en').values()
    countries.sort()

    categories = FunctionalArea.active_objects.all()

    initiatives = Campaign.active_objects.all()

    reps = (User.objects.filter(userprofile__registration_complete=True, groups__name='Rep')
                        .order_by('userprofile__country', 'last_name', 'first_name'))

    return render(request, 'kpi.jinja',
                  {'reps': reps, 'countries': countries,
                   'categories': categories, 'initiatives': initiatives})
