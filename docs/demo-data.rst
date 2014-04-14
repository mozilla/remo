====================================
Creating demo data using factories
====================================

In order to populate our development environment with data
in an automated way, we have implemented model factories using
`Factory Boy <https://github.com/rbarrois/factory_boy>`_.

Factory Boy is a fixtures replacement for Python. For
more details visit the `project's documentation
<https://factoryboy.readthedocs.org/en/latest/>`_.

Using factories
---------------
By default, model factories get instantiated using the associated model fields.
On top of that we provide additional :ref:`attributes <classes>` to add extra
functionality in object creation. For example:

- To create a single model object from a factory class (eg. ``UserFactory``)
  use the ``create()`` method:

   ``user = UserFactory.create()``

- To create multiple model objects at once (eg. 10) use the ``create_batch()``
  method:

   ``users = UserFactory.create_batch(10)``

- To customize your demo data you can override model attributes
  (eg. ``username``):

   ``user = UserFactory.create(username='example')``

.. _classes:

``remo`` factory classes
--------------------------
Here is the list of the implemented model factories we have in ``remo``
and their associated `PostGeneration methods
<https://factoryboy.readthedocs.org/en/factory_boy-1.2.0/post_generation.html>`_
that help in some complex definitions of our models.

``remo.profiles`` factory classes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ``UserFactory``
   - ``groups``: List of strings with group names to add to user groups
      (eg. ``['Rep', 'Council']``)

- ``UserProfileFactory``
   - ``functional_areas``: List of ``FunctionalArea`` objects to add to
     user functional areas

   - ``random_functional_areas``: ``Boolean``. Populates ``UserProfile``
     with random functional areas of random length.

   - ``initial_council``: ``Boolean``. ``UserProfile`` object has itself
     as mentor.

- ``FunctionalAreaFactory``

``remo.events`` factory classes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ``EventFactory``
   - ``categories``: List of ``FunctionalArea`` objects to add to event
     categories.
   - ``random_categories``: ``Boolean``
- ``AttendanceFactory``


``remo.reports`` factory classes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ``NGReportFactory``
- ``ActivityFactory``
- ``CampaignFactory``

``remo.remozilla`` factory classes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ``BugFactory``
   - ``add_cc_users``: List of users to add to bug cc field

``remo.voting`` factory classes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ``PollFactory``
- ``VoteFactory``
- ``RadioPollFactory``
- ``RadioPollChoiceFactory``
- ``RangePollFactory``
- ``RangePollChoiceFactory``


Factory examples
-----------------

- To ``create_batch`` of users (eg. 10) with random functional areas that
  belong to the initial council ::

     from remo.profiles.tests import UserFactory

     kwargs = {
         'groups': ['Reps', 'Mentor', 'Council'],
         'userprofile__random_functional_areas': True,
         'userprofile__initial_council': True
     }

     users = UserFactory.create_batch(10, **kwargs)

- To ``create_batch`` of past events (eg. 10) with random categories and
  10 attendees ::

    from remo.events.tests import EventFactory, AttendanceFactory

    events = EventFactory.create_batch(10, random_categories=True)

    for event in events:
        AttendanceFactory.create_batch(10, event=event)

  .. note::

    The above script creates new users for ``event.owner``,
    ``event.attendance.user`` and new swag and budget bugs.

- To ``create`` a poll with 10 radio and range poll choices ::

    from remo.voting.tests import *

    poll = PollFactory.create()

    radio_poll = RadioPollFactory.create(poll=poll)
    range_poll = RangePollFactory.create(poll=poll)

    radio_poll_choices = RadioPollChoiceFactory.create_batch(10, radio_poll=radio_poll)
    range_poll_choices = RangePollChoiceFactory.create_batch(10, range_poll=range_poll)
