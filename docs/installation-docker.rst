===================
Docker Installation
===================

Getting your own development environment.

Preparing Your System
---------------------

**Prerequisites:** You 'll need to install docker and docker-compose in your system.

#. **Install prerequisites:**

   Most Linux distributions come with a packaged version for docker and docker-compose.

   - For debian based systems::

     $ sudo apt-get install docker.io docker-compose

   For other Linux distributions, you can consult the `installation guide <https://docs.docker.com/installation/#installation>`_.
   More information about docker-compose can be found `here <https://docs.docker.com/compose/>`_.



Build the Environment
---------------------

When you want to start contributing...

#. **Clone ReMo repository.**

   Mozilla Reps Portal is hosted on `<https://github.com/mozilla/remo>`_.

   Clone the repository locally::

     $ git clone --recursive https://github.com/mozilla/remo


   .. note::

      Make sure you use ``--recursive`` when checking the repo out!
      If you didn't, you can load all the submodules with ``git
      submodule update --init --recursive``.

#. **Configure your local ReMo installation.**::

     (venv)$ cp settings/local.py-docker-dist settings/local.py

#. Update the product details::

     $ docker-compose run web python manage.py update_product_details -f

#. Create the database tables and run the migrations::

     $ docker-compose run web python manage.py syncdb --noinput --migrate

#. Create an admin account.

   Create your own admin account::

    $ docker-compose run web ./manage.py createsuperuser

************
Running ReMo
************

#. Run ReMo::

     $ docker-compose up
     (lots of output - be patient...)

#. Develop!
