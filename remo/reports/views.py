from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now
from django.views.decorators.cache import never_cache

from django_statsd.clients import statsd

import forms
from remo.base.decorators import permission_check
from remo.base.templatetags.helpers import urlparams
from remo.base.utils import month2number
from remo.profiles.models import FunctionalArea, UserProfile
from remo.reports import ACTIVITY_CAMPAIGN, UNLISTED_ACTIVITIES
from remo.reports.models import NGReport, NGReportComment


# New reporting system
LIST_NG_REPORTS_DEFAULT_SORT = 'created_date_desc'
LIST_NG_REPORTS_VALID_SORTS = {
    'reporter_desc': '-user__last_name,user__first_name',
    'reporter_asc': 'user__last_name,user__first_name',
    'mentor_desc': '-mentor__last_name,mentor__first_name',
    'mentor_asc': 'mentor__last_name,mentor__first_name',
    'activity_desc': '-activity__name',
    'activity_asc': 'activity__name',
    'report_date_desc': '-report_date',
    'report_date_asc': 'report_date',
    'created_date_desc': '-created_on',
    'created_date_asc': 'created_on'}


@never_cache
@permission_check(permissions=['reports.add_ngreport', 'reports.change_ngreport'],
                  filter_field='display_name', owner_field='user', model=UserProfile)
def edit_ng_report(request, display_name='', year=None, month=None, day=None, id=None):
    user = request.user
    created = False
    initial = {}

    if not id:
        report = NGReport()
        created = True
        initial = {'location': '%s, %s, %s' % (user.userprofile.city,
                                               user.userprofile.region,
                                               user.userprofile.country),
                   'latitude': user.userprofile.lat,
                   'longitude': user.userprofile.lon}
    else:
        report = get_object_or_404(NGReport, pk=id, user__userprofile__display_name=display_name)

    if not created and report.activity.name in UNLISTED_ACTIVITIES:
        messages.warning(request, 'You cannot edit this report.')
        return redirect(report.get_absolute_url())

    report_form = forms.NGReportForm(request.POST or None, instance=report, initial=initial)
    if report_form.is_valid():
        if created:
            report.user = user
            messages.success(request, 'Report successfully created.')
            statsd.incr('reports.create_report')
        else:
            messages.success(request, 'Report successfully updated.')
            statsd.incr('reports.edit_report')
        report_form.save()
        return redirect(report.get_absolute_url())

    return render(request, 'edit_ng_report.jinja',
                  {'report_form': report_form,
                   'pageuser': user,
                   'report': report,
                   'created': created,
                   'campaign_trigger': ACTIVITY_CAMPAIGN})


def view_ng_report(request, display_name, year, month, day=None, id=None):
    if not day and not id:
        url = reverse('list_ng_reports_rep', kwargs={'rep': display_name})
        return redirect(urlparams(url, year=year, month=month))

    user = get_object_or_404(User, userprofile__display_name=display_name)
    report = get_object_or_404(NGReport, id=id)
    comment_form = forms.NGReportCommentForm()
    verification_form = forms.NGVerifyReportForm(instance=report)

    editable = False
    if (((request.user == user or request.user.has_perm('change_ngreport')) and
         (report.activity.name not in UNLISTED_ACTIVITIES))):
        editable = True

    ctx_data = {'pageuser': user,
                'user_profile': user.userprofile,
                'report': report,
                'editable': editable,
                'comment_form': comment_form,
                'verification_form': verification_form}
    template = 'view_ng_report.jinja'

    if request.method == 'POST':
        # Process comment form
        if 'comment' in request.POST:
            comment_form = forms.NGReportCommentForm(request.POST)
            if comment_form.is_valid():
                if not request.user.is_authenticated():
                    messages.error(request, 'Permission denied.')
                    return redirect('main')
                obj = comment_form.save(commit=False)
                obj.user = request.user
                obj.report = report
                obj.save()
                messages.success(request, 'Comment saved successfully.')
                statsd.incr('reports.create_comment')
                ctx_data['comment_form'] = forms.NGReportCommentForm()

        # Process verification form
        else:
            verification_form = forms.NGVerifyReportForm(request.POST, instance=report)
            if verification_form.is_valid():
                if ((not request.user.is_authenticated()) or
                    (not request.user.groups.filter(
                        Q(name='Council') | Q(name='Mentor')).exists())):
                    messages.error(request, 'Permission denied.')
                    return redirect('main')
                if verification_form.cleaned_data['verified_activity']:
                    messages.success(request, u'Activity verified successfully.')
                else:
                    messages.success(request, u'Activiy invalidated successfully.')
                verification_form.save()
                ctx_data['verification_form'] = forms.NGVerifyReportForm(instance=report)

    return render(request, template, ctx_data)


@never_cache
@permission_check(permissions=['reports.delete_ngreport'],
                  filter_field='display_name', owner_field='user', model=UserProfile)
def delete_ng_report(request, display_name, year, month, day, id):
    user = get_object_or_404(User, userprofile__display_name=display_name)
    if request.method == 'POST':
        report = get_object_or_404(NGReport, id=id)
        report.delete()
        messages.success(request, 'Report successfully deleted.')
        statsd.incr('reports.delete_report')

    if request.user == user:
        return redirect('profiles_view_my_profile')
    return redirect('profiles_view_profile', display_name=display_name)


@permission_check(permissions=['reports.delete_ngreportcomment'],
                  filter_field='display_name', owner_field='user', model=UserProfile)
def delete_ng_report_comment(request, display_name, year, month, day, id, comment_id):
    report = get_object_or_404(NGReport, pk=id)
    if comment_id and request.method == 'POST':
        report_comment = get_object_or_404(NGReportComment, pk=comment_id)
        report_comment.delete()
        messages.success(request, 'Comment successfully deleted.')
        statsd.incr('reports.delete_comment')
    return redirect(report.get_absolute_url())


def list_ng_reports(request, mentor=None, rep=None, functional_area_slug=None):
    today = now().date()
    report_list = NGReport.objects.filter(report_date__lte=today)
    pageheader = 'Activities for Reps'
    user = None
    pageuser_is_mentor = False

    if mentor or rep:
        user = get_object_or_404(User, userprofile__display_name__iexact=mentor or rep)

        if mentor:
            report_list = report_list.filter(mentor=user)
            pageheader += ' mentored by %s' % user.get_full_name()
            pageuser_is_mentor = True
        elif rep:
            report_list = report_list.filter(user=user)
            pageheader = 'Activities for %s' % user.get_full_name()

    if functional_area_slug:
        functional_area = get_object_or_404(FunctionalArea, slug=functional_area_slug)
        report_list = report_list.filter(functional_areas=functional_area)
        pageheader += ' for area %s' % functional_area.name

    month = request.GET.get('month')
    year = request.GET.get('year')
    if month and year:
        try:
            month = month2number(month)
            # Make sure that year is an integer too
            year = int(year)
        except (TypeError, ValueError):
            raise Http404()
        report_list = report_list.filter(report_date__year=year, report_date__month=month)

    if 'query' in request.GET:
        query = request.GET['query'].strip()
        report_list = report_list.filter(
            Q(ngreportcomment__comment__icontains=query) |
            Q(activity__name__icontains=query) |
            Q(activity_description__icontains=query) |
            Q(campaign__name__icontains=query) |
            Q(functional_areas__name__icontains=query) |
            Q(location__icontains=query) |
            Q(link__icontains=query) |
            Q(link_description__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__userprofile__local_name__icontains=query) |
            Q(user__userprofile__display_name__icontains=query) |
            Q(mentor__first_name__icontains=query) |
            Q(mentor__last_name__icontains=query) |
            Q(mentor__userprofile__local_name__icontains=query) |
            Q(mentor__userprofile__display_name__icontains=query))

    report_list = report_list.distinct()
    number_of_reports = report_list.count()

    sort_key = request.GET.get('sort_key', LIST_NG_REPORTS_DEFAULT_SORT)
    if sort_key not in LIST_NG_REPORTS_VALID_SORTS:
        sort_key = LIST_NG_REPORTS_DEFAULT_SORT

    sort_by = LIST_NG_REPORTS_VALID_SORTS[sort_key]
    report_list = report_list.order_by(*sort_by.split(','))

    paginator = Paginator(report_list, settings.ITEMS_PER_PAGE)

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        reports = paginator.page(page)
    except (EmptyPage, InvalidPage):
        reports = paginator.page(paginator.num_pages)

    return render(request, 'list_ng_reports.jinja',
                  {'objects': reports,
                   'number_of_reports': number_of_reports,
                   'sort_key': sort_key,
                   'pageheader': pageheader,
                   'pageuser': user,
                   'pageuser_is_mentor': pageuser_is_mentor,
                   'query': request.GET.get('query', '')})
