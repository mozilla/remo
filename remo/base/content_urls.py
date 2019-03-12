from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse_lazy

from remo.base.views import BaseCreateView, BaseListView, BaseUpdateView
from remo.events.models import EventMetric
from remo.events.forms import EventMetricForm
from remo.profiles.forms import FunctionalAreaForm, MobilisingSkillForm, MobilisingInterestForm
from remo.profiles.models import FunctionalArea, MobilisingSkill, MobilisingInterest
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
    url(r'^activities/(?P<pk>\d+)/edit/$',
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
    url(r'^initiatives/(?P<pk>\d+)/edit/$',
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
    url(r'^functional_areas/(?P<pk>\d+)/edit/$',
        BaseUpdateView.as_view(
            model=FunctionalArea, form_class=FunctionalAreaForm,
            success_url=reverse_lazy('list_functional_areas')),
        name='edit_functional_area'),
    url('^mobilising_skills/$',
        BaseListView.as_view(
            groups=['Admin', 'Council'],
            model=MobilisingSkill,
            create_object_url=reverse_lazy('create_mobilising_skills')),
        name='list_mobilising_skills'),
    url('^mobilising_skills/new/$',
        BaseCreateView.as_view(
            groups=['Admin', 'Council'],
            model=MobilisingSkill, form_class=MobilisingSkillForm,
            success_url=reverse_lazy('list_mobilising_skills')),
        name='create_mobilising_skills'),
    url(r'^mobilising_skills/(?P<pk>\d+)/edit/$',
        BaseUpdateView.as_view(
            groups=['Admin', 'Council'],
            model=MobilisingSkill, form_class=MobilisingSkillForm,
            success_url=reverse_lazy('list_mobilising_skills')),
        name='edit_mobilising_skills'),
    url('^mobilising_interests/$',
        BaseListView.as_view(
            groups=['Admin', 'Council'],
            model=MobilisingInterest,
            create_object_url=reverse_lazy('create_mobilising_interests')),
        name='list_mobilising_interests'),
    url('^mobilising_interests/new/$',
        BaseCreateView.as_view(
            groups=['Admin', 'Council'],
            model=MobilisingInterest, form_class=MobilisingInterestForm,
            success_url=reverse_lazy('list_mobilising_interests')),
        name='create_mobilising_interests'),
    url(r'^mobilising_interests/(?P<pk>\d+)/edit/$',
        BaseUpdateView.as_view(
            groups=['Admin', 'Council'],
            model=MobilisingSkill, form_class=MobilisingInterestForm,
            success_url=reverse_lazy('list_mobilising_interests')),
        name='edit_mobilising_interests'),
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
    url(r'^metrics/(?P<pk>\d+)/edit/$',
        BaseUpdateView.as_view(
            groups=['Admin', 'Council'],
            model=EventMetric, form_class=EventMetricForm,
            success_url=reverse_lazy('list_metrics')),
        name='edit_metric'),
)
