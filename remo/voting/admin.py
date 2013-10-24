from django.contrib import admin

from models import (Poll, RadioPoll, RadioPollChoice,
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


class RadioPollInline(admin.StackedInline):
    """Poll Radio Inline."""
    model = RadioPoll
    extra = 0


class RadioPollAdmin(admin.ModelAdmin):
    inlines = [RadioPollChoiceInline]


class RangePollAdmin(admin.ModelAdmin):
    inlines = [RangePollChoiceInline]


class PollAdmin(admin.ModelAdmin):
    """Voting Admin."""
    inlines = [RangePollInline, RadioPollInline]
    search_fields = ['name']
    list_display = ['name', 'start', 'end', 'valid_groups']
    date_hierarchy = 'start'
    readonly_fields = ['task_start_id', 'task_end_id', 'last_notification',
                       'bug']
    list_filter = ['automated_poll']


class VoteAdmin(admin.ModelAdmin):
    """Vote Admin"""
    model = Vote


admin.site.register(Vote, VoteAdmin)
admin.site.register(RangePoll, RangePollAdmin)
admin.site.register(RadioPoll, RadioPollAdmin)
admin.site.register(Poll, PollAdmin)
