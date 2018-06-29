=====================================
Reset specific user password by shell
=====================================

In case you don't remember the user password it is easy to do change by CLI. For example:

- Run the shell mode in Django:

   ``docker-compose run --rm web ./manage.py shell``

- After loading you will be in the shell mode where you can run python code:

    .. code-block:: python

       from django.contrib.auth.models import User #import the class
       # users = User.objects.all() # to get the list of all the accounts with their public names
       user = User.objects.get(email='user_email')
       user.set_password('__enter passwd__')
       user.username # to get the username for the login
       user.save()
       exit
    ....