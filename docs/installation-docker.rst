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

     $ cp env-dist .env

#. Update the product details::

     $ docker-compose run web python manage.py update_product_details -f

#. Create the database tables and run the migrations::

     $ docker-compose run web python manage.py migrate --noinput

#. Create your own admin account::

    $ docker-compose run web ./manage.py createsuperuser

#. Add demo users::

    $ docker-compose run web ./manage.py loaddata demo_users

#. Add demo functional areas::

    $ docker-compose run web ./manage.py loaddata demo_functional_areas

#. Add demo mobilizing expertise::

    $ docker-compose run web ./manage.py loaddata demo_mobilising_skills

#. Add demo mobilizing learning interests::

    $ docker-compose run web ./manage.py loaddata demo_mobilising_interests

#. Add demo events::

    $ docker-compose run web ./manage.py loaddata demo_events

************
Running ReMo
************

#. Run ReMo::

     $ docker-compose up
     (lots of output - be patient...) or
     $ docker-compose run --rm --service-ports web
     (this enables the output of print() on the docker output)

#. Open the `local site <http://127.0.0.1:8000>`_ and develop!

#. Run tests::

     $ docker-compose run web ./manage.py test
