===================
Docker Installation
===================

Getting your own development environment.

Preparing Your System
---------------------

#. You need to install docker in your system. The `installation guide <https://docs.docker.com/installation>`_ covers many operating systems but for now we only support Linux.

#. We are using an orchestration tool for docker called `docker-compose <https://docs.docker.com/compose//>`_ that helps us automate the procedure of initiating our docker containers required for development. Installation instructions can be found `in Compose's documentation <https://docs.docker.com/compose/install/>`_. *Version required*: 1.0.1 or newer.


Build the Environment
---------------------

When you want to start contributing...
#. `Fork the main ReMo repository <https://github.com/mozilla/remo>`_.
#. Clone your fork to your local machine::

     $ git clone git@github.com:YOUR_USERNAME/remo.git remo
     (lots of output - be patient...)
     $ cd remo

#. Configure your local ReMo installation::

     $ cp remo/settings/local.py-docker-dist remo/settings/local.py

#. Choose a HMAC_KEY.

   For development purposes you can uncomment the key '2012-06-15'
   with HMAC_KEYS dictionary in your *local.py*::

     HMAC_KEYS = {
        '2012-06-15': 'some key',
     }

#. Update the product details::

     $ docker-compose run web python manage.py update_product_details -f

#. Create the database tables and run the migrations::

     $ docker-compose run web python manage.py migrate --noinput

#. Create an admin account.

   Create your own admin account::

    $ docker-compose run web ./manage.py createsuperuser

#. Add demo users.::

    $ docker-compose run web ./manage.py loaddata demo_users

#. Add demo functional areas.::

    $ docker-compose run web ./manage.py loaddata demo_functional_areas

#. Add demo events.::

    $ docker-compose run web ./manage.py loaddata demo_events

************
Running ReMo
************

#. Run ReMo::

     $ docker-compose up
     (lots of output - be patient...)

#. Develop!
