========
Profiles
========

Profiles store information about the Reps.

Fields
------

We are collecting the following information for each Rep:

 * First Name
 * Last Name
 * Birth Year
 * City
 * Region
 * Country
 * Longitude, Latitude
 * Display Name
 * Mozillians Profile
 * Private Email
 * Bugzilla Email
 * Twitter Account
 * GPG-Key
 * Jabber ID
 * IRC Nickname
 * IRC Channels in irc.m.o
 * LinkedIn Profile URL
 * Diaspora Profile URL
 * Facebook Profile URL
 * Personal Website URL
 * Personal Blog Feed
 * Rep Status (Admin, Counselor, Mentor, Rep)

Avatar
------

The portal does not provide functionality for users to upload or
change avatar images. User's avatar is directly fetched from `Gravatar
<http://gravatar.com>`_ by hashing user's bugzilla email.

Registration and Login
----------------------

All Mozilla Reps are able to login into the ReMo Portal using their
bugzilla email address and `BrowerID <https://browserid.org>`_. No
registration is required. Users that are not approved Mozilla Reps
will not be able to login.

Creating new account for a Rep
------------------------------

Administrators and Mentors can create accounts for Reps using the
*Account creation form*. The form must be filled with the bugzilla
email of the Rep that owns the new account.

The new account is not activated on creation. User has to login
within two weeks to activate the account.

On creation Rep receives an invitation email to join the portal.

Creating new accounts en-masse
------------------------------

New accounts can be created massivelly using the following command::

 $ python manage.py create_users <user_list.txt>

The *user_list.txt* parameter is a plain text file containing bugzilla
email addresses of Reps, one per line like this::

  foo@bar.com
  python@snakes.org
  yummy@goodness.net

Accounts are not activated on creation. User has to login within two
weeks to activate the account.

On creation Rep receives an invitation email to join the portal.

Creating Demo accounts for testing
----------------------------------

The following command::

 $ python manage.py loaddata demo_users

creates a number of demo accounts with different permissions::

  +-----------+-----------------------+----------+---------------+
  | Username  | Email                 | Password | Level         |
  +===========+=======================+==========+===============+
  | admin     | admin@example.com     | passwd   | Administrator |
  | counselor | counselor@example.com | passwd   | Counselor     |
  | mentor    | mentor@example.com    | passwd   | Mentor        |
  | rep       | rep@example.com       | passwd   | Rep           |
  | rep2      | rep2@example.com      | passwd   | Inactive Rep  |
  +-----------+-----------------------+----------+---------------+

.. warning::

   Do *not* run this command on production servers as it will impose
   serious security risks.


Data Migration from Wiki
------------------------

Lots of ReMo information already exists in `Mozilla's Wiki
<https://wiki.mozilla.com/ReMo>`_. Information can be one-way
synchronized from wiki using the following command::

  $ python manage.py wiki_migrate

Information is fetched using `MediaWiki Ask API extension
<https://secure.wikimedia.org/wikipedia/mediawiki/wiki/Extension:SMWAskAPI>`_. Only
new profiles will be created, existing profile will not be edited.


API
---

Profiles App provides an API for other applications to receive data
releated to Mozilla Reps.

.. TODO: autodocument from api
