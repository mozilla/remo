===================
FAQ
===================

Persona Login not work (500 Error)
--------

You need to check the config on your local.py file, if the SITE_URL contain 127.0.0.1 you have to use that domain instead localhost.


Persona Login Redirect Loop
-----------------------------

You need to enter in shell mode:

#. **Docker** for the shell

     ~$ docker-compose run web python manage.py shell

#. **Insert that commands**::

     ~$ from remo.profiles.models import UserProfile
     ~$ user = UserProfile.objects.get(user__email='your@email.here')
     ~$ user.registration_complete = True
     ~$ user.save()

Change the email with the superadmin email, after the login go to http://localhost:8000/admin/auth/user/ and fill all the required fields.

