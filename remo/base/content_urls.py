from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse_lazy

from remo.base.views import BaseCreateView, BaseListView, BaseUpdateView
from remo.events.models import EventMetric
from remo.events.forms import EventMetricForm
from remo.profiles.forms import FunctionalAreaForm
from remo.profiles.models import FunctionalArea
from remo.reports.forms import ActivityForm, CampaignForm
from remo.reports.models import Activity, Campaign


urlpatterns = patterns(
    '',
    url('^activities/$',
        BaseListView.as_view(
            groups=['Admin', 'Council'],
            model=Activity, create_object_url=reverse_lazy('create_activity')),
        name='list_activities'),
    url('^activities/new/$',
        BaseCreateView.as_view(
            groups=['Admin', 'Council'],
            model=Activity, form_class=ActivityForm,
            success_url=reverse_lazy('list_activities')),
        name='create_activity'),
    url('^activities/(?P<pk>\d+)/edit/$',
        BaseUpdateView.as_view(
            groups=['Admin', 'Council'],
            model=Activity, form_class=ActivityForm,
            success_url=reverse_lazy('list_activities')),
        name='edit_activity'),
    url('^initiatives/$',
        BaseListView.as_view(
            groups=['Admin', 'Council'],
            model=Campaign, create_object_url=reverse_lazy('create_campaign')),
        name='list_campaigns'),
    url('^initiatives/new/$',
        BaseCreateView.as_view(
            groups=['Admin', 'Council'],
            model=Campaign, form_class=CampaignForm,
            success_url=reverse_lazy('list_campaigns')),
        name='create_campaign'),
    url('^initiatives/(?P<pk>\d+)/edit/$',
        BaseUpdateView.as_view(
            groups=['Admin', 'Council'],
            model=Campaign, form_class=CampaignForm,
            success_url=reverse_lazy('list_campaigns')),
        name='edit_campaign'),
    url('^functional_areas/$',
        BaseListView.as_view(
            model=FunctionalArea,
            create_object_url=reverse_lazy('create_functional_area')),
        name='list_functional_areas'),
    url('^functional_areas/new/$',
        BaseCreateView.as_view(
            model=FunctionalArea, form_class=FunctionalAreaForm,
            success_url=reverse_lazy('list_functional_areas')),
        name='create_functional_area'),
    url('^functional_areas/(?P<pk>\d+)/edit/$',
        BaseUpdateView.as_view(
            model=FunctionalArea, form_class=FunctionalAreaForm,
            success_url=reverse_lazy('list_functional_areas')),
        name='edit_functional_area'),
    url('^metrics/$',
        BaseListView.as_view(
            model=EventMetric,
            create_object_url=reverse_lazy('create_metric'),
            groups=['Admin', 'Council']),
        name='list_metrics'),
    url('^metrics/new/$',
        BaseCreateView.as_view(
            groups=['Admin', 'Council'],
            model=EventMetric, form_class=EventMetricForm,
            success_url=reverse_lazy('list_metrics')),
        name='create_metric'),
    url('^metrics/(?P<pk>\d+)/edit/$',
        BaseUpdateView.as_view(
            groups=['Admin', 'Council'],
            model=EventMetric, form_class=EventMetricForm,
            success_url=reverse_lazy('list_metrics')),
        name='edit_metric'),
)
