from django.contrib import admin

from models import Poll, PollRange, PollRangeVotes, PollRadio, PollChoices


# Poll Range
class PollRangeVotesInline(admin.StackedInline):
    """Poll Range Votes Inline."""
    model = PollRangeVotes
    extra = 2


class PollRangeInline(admin.StackedInline):
    """Poll Range Inline."""
    model = PollRange
    extra = 1


# Radio votes
class PollChoicesInline(admin.StackedInline):
    """Poll Choices Inline."""
    model = PollChoices
    extra = 1


class PollRadioInline(admin.StackedInline):
    """Poll Radio Inline."""
    model = PollRadio
    extra = 1


class PollRadioAdmin(admin.ModelAdmin):
    inlines = [PollChoicesInline]


class PollRangeAdmin(admin.ModelAdmin):
    inlines = [PollRangeVotesInline]


class PollAdmin(admin.ModelAdmin):
    """Voting Admin."""
    inlines = [PollRangeInline, PollRadioInline]
    search_fields = ['name']
    date_hierarchy = 'created_on'


admin.site.register(PollRange, PollRangeAdmin)
admin.site.register(PollRadio, PollRadioAdmin)
admin.site.register(Poll, PollAdmin)
