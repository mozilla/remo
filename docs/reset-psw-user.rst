====================================
Reset specific user password by shell
====================================


---------------
In case you don't remember the user password it is easy to do change by CLI. For example:

- Run the shell mode in Django:

   ``docker-compose run --rm web ./manage.py shell``

- To create multiple model objects at once (eg. 10) use the ``create_batch()``
  method:

   ``from django.contrib.auth.models import User #import the class
     users = User.objects.filter()
     users # will show the list of accounts with their public names
     user=users[0] # with this example we take the first user
     user.set_password('__enter passwd__')
     user.username # to get the username for the login
     user.save()
     exit
``
