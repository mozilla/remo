=======================
VirtualEnv Installation
=======================

Getting your own development environment.

Preparing Your System
---------------------

**Prerequisites:** You 'll need python, virtualenv, pip, git and mysql-server.

- For debian based systems::

   $ sudo apt-get install python-dev python-pip python-virtualenv git mysql-server libmysqlclient-dev \
     libxslt1.1 libxml2 libxml2-dev libxslt1-dev libffi-dev

For other Linux distributions, you can consult the documentation of your distribution.


Build the Environment
---------------------

When you want to start contributing...

#.  `Fork the main ReMo repository`_ (https://github.com/mozilla/remo) on GitHub.

#.  Clone your fork to your local machine::

       $ git clone git@github.com:YOUR_USERNAME/remo.git remo
       (lots of output - be patient...)


#. Create your python virtual environment.::

   $ cd remo/
   $ virtualenv --no-site-packages venv


#. Activate your python virtual environment.::

   $ source venv/bin/activate

#. Install development requirements.::

     (venv)$ python ./bin/pipstrap.py
     (venv)$ pip install --require-hashes --no-deps -r requirements/dev.txt

   .. note::

      When you activate your python virtual environment 'venv'
      (virtual environment's root directory name) will be prepended
      to your PS1.


   .. note::

      Since you are using a virtual environment all the python
      packages you will install while the environment is active,
      will be available only within this environment. Your system's
      python libraries will remain intact.


#. Configure your local ReMo installation.::

     (venv)$ cp env-dist .env


#. Activate MailHide.

   We use `MailHide
   <https://developers.google.com/recaptcha/docs/mailhideapi>`_ to
   protect our users from spam. Open `local.py` under `settings`
   directory and uncomment the following lines::

     # MAILHIDE_PUB_KEY = '02Ni54q--g1yltekhaSmPYHQ=='
     # MAILHIDE_PRIV_KEY = 'fe55a9921917184732077e3fed19d0be'

   These keys are `demo` keys and will not decrypt emails on your
   local installation but that's OK if you are not working on a
   related bug.

   If you are to work on a MailHide related bug, register on
   `MailHide's website
   <http://www.google.com/recaptcha/mailhide/apikey>`_ for a valid
   pair of keys.


#. Setting up a MySQL database for development:

   Install the MySQL server. Many Linux distributions provide an installable
   package. If your OS does not, you can find downloadable install packages
   on the `MySQL site`_.

#. Start the mysql client program as the mysql root user::

    $ mysql -u root -p
    Enter password: ........
    mysql>

#. Create a ``remo`` database::

    mysql> create database remo character set utf8;

#. Sync DB.::

     (venv)$ ./manage.py migrate --noinput


#. Create an admin account.

   Create your own admin account::

    (venv)$ ./manage.py createsuperuser


#. Update product_details package.

   Package `product_details` provides information about countries. We
   use it in country selection lists. The information get pulled form
   mozilla's SVN, so we need to fetch it at least once. To update run::

     (venv)$ ./manage.py update_product_details


#. Collect static files.

   Various packages provide static files. We need to collect them in
   the STATIC_DIR::

     (venv)$ ./manage.py collectstatic


#. Load demo data (optional).

   Depending on what you are going to develop you may need to have
   some demo data.

   To load *demo users* run (within your virtual env)::

     (venv)$ ./manage.py loaddata demo_users

   To load *demo functional areas* run::

     (venv)$ ./manage.py loaddata demo_functional_areas

   To load *demo mobilising skills* run::

     (venv)$ ./manage.py loaddata demo_mobilising_skills

   To load *demo mobilising interests* run::

     (venv)$ ./manage.py loaddata demo_mobilising_interests

   To load *demo events* run::

     (venv)$ ./manage.py loaddata demo_events

   To fetch *bugzilla bugs* run::

     (venv)$ ./manage.py fetch_bugs

   .. note::

      Fetching bugzilla bug requires a Mozilla Reps Admin account on
      Bugzilla. Ping `nemo-yiannis` or `tasos` on #remo-dev to give you access if
      your project requires it.

.. _MySQL site: http://dev.mysql.com/downloads/mysql/
.. _Fork the main ReMo repository: https://github.com/mozilla/remo/fork
