from django.contrib import admin

from import_export.admin import ExportMixin
from models import (Poll, PollComment,  RadioPoll, RadioPollChoice,
                    RangePoll, RangePollChoice, Vote)


class RangePollChoiceInline(admin.StackedInline):
    """Poll Range Votes Inline."""
    model = RangePollChoice
    extra = 0
    readonly_fields = ['votes']


class RangePollInline(admin.StackedInline):
    """Range Poll Inline."""
    model = RangePoll
    extra = 0


class RadioPollChoiceInline(admin.StackedInline):
    """Radio Poll Choice Inline."""
    model = RadioPollChoice
    extra = 0
    readonly_fields = ['votes']


class RadioPollInline(admin.StackedInline):
    """Poll Radio Inline."""
    model = RadioPoll
    extra = 0


class RadioPollAdmin(ExportMixin, admin.ModelAdmin):
    inlines = [RadioPollChoiceInline]


class RangePollAdmin(ExportMixin, admin.ModelAdmin):
    inlines = [RangePollChoiceInline]


class PollCommentInline(admin.StackedInline):
    """PollComment Inline."""
    model = PollComment


class PollAdmin(ExportMixin, admin.ModelAdmin):
    """Voting Admin."""
    inlines = [RangePollInline, RadioPollInline, PollCommentInline]
    search_fields = ['name']
    list_display = ['name', 'start', 'end', 'valid_groups']
    date_hierarchy = 'start'
    readonly_fields = ['task_start_id', 'task_end_id', 'bug']
    list_filter = ['automated_poll']


class VoteAdmin(ExportMixin, admin.ModelAdmin):
    """Vote Admin"""
    model = Vote


admin.site.register(Vote, VoteAdmin)
admin.site.register(RangePoll, RangePollAdmin)
admin.site.register(RadioPoll, RadioPollAdmin)
admin.site.register(Poll, PollAdmin)
