from datetime import datetime

from django.shortcuts import get_object_or_404, render

from remo.base.decorators import permission_check
from remo.voting.models import Poll


@permission_check()
def list_votings(request):
    """List votings view."""
    user = request.user
    now = datetime.now()
    polls = Poll.objects.all()
    if not user.groups.filter(name='Admin').exists():
        polls = Poll.objects.filter(valid_groups__in=user.groups.all())

    past_polls = polls.filter(end__lt=now)
    current_polls = polls.filter(start__lt=now, end__gt=now)
    future_polls = polls.filter(start__gt=now)

    return render(request, 'list_votings.html',
                  {'user': user,
                   'past_polls': past_polls,
                   'current_polls': current_polls,
                   'future_polls': future_polls})


@permission_check(group='Admin')
def edit_voting(request, slug=None):
    """Create/Edit voting view."""
    return render(request, 'edit_voting.html')


@permission_check()
def view_voting(request, slug):
    """View voting view."""
    voting = get_object_or_404(Poll, slug=slug)
    return render(request, 'view_voting.html', {'voting': voting})
