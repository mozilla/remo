=======================
VirtualEnv Installation
=======================

Getting your own development environment.

Preparing Your System
---------------------

**Prerequisites:** You 'll need python, virtualenv, pip, git and mysql-server.

#. **Install prerequisites:**

   Most Linux distributions come with a packaged version for all the prerequisites.

   - For debian based systems::

     $ sudo apt-get install python-pip python-virtualenv git mysql-server libmysqlclient-dev libxslt1.1 libxml2 libxml2-dev

   For other Linux distributions, you can consult the documentation of your distribution.


Build the Environment
---------------------

When you want to start contributing...

#. **Clone ReMo repository.**

   Mozilla Reps Portal is hosted on `<http://github.com/mozilla/remo>`_.

   Clone the repository locally::

     $ git clone --recursive http://github.com/mozilla/remo


   .. note::

      Make sure you use ``--recursive`` when checking the repo out!
      If you didn't, you can load all the submodules with ``git
      submodule update --init --recursive``.


#. **Create your python virtual environment.**::

   $ cd remo/
   $ virtualenv --no-site-packages venv


#. **Activate your python virtual environment.**::

   $ source venv/bin/activate

#. **Install development and compiled requirements.**::

     (venv)$ pip install -r requirements/dev.txt

   .. note::

      When you activate your python virtual environment 'venv'
      (virtual environment's root directory name) will be prepended
      to your PS1.


   .. note::

      Since you are using a virtual environment all the python
      packages you will install while the environment is active,
      will be available only within this environment. Your system's
      python libraries will remain intact.

#. **Create the database.**
   
   The provided configuration assumes a database with the
   name `remo` for user `root` with password `root`
   and the server listens to `127.0.0.1:8000`. 
   So, it is important not to forget to create the database 
   `remo` in your mysql server and add your root password 
   to your local.py file. You can alter the configuration 
   to fit your own needs.

   For example for user `root` with password `root`::

   $ mysql -uroot -proot -B -e 'CREATE DATABASE remo CHARACTER SET utf8;'

#. **Configure your local ReMo installation.**::

     (venv)$ cp settings/local.py-dist settings/local.py

#. **Choose a HMAC_KEY.**

   For development purposes you can uncomment the key '2012-06-15'
   with HMAC_KEYS dictionary in your *local.py*::

    HMAC_KEYS = {
       '2012-06-15': 'some key',
    }


#. **Set SITE_URL.**

   For development purposes you can uncomment the line::

     SITE_URL = 'http://127.0.0.1:8000'

   in your *local.py* or BrowserID will fail to log you in.

#. **Activate MailHide.**

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


#. **Sync DB.**::

     (venv)$ ./manage.py syncdb && ./manage.py migrate


#. **Create an admin account.**

   Within your vagrant machine, create your own admin account::

    (venv)$ ./manage.py createsuperuser


   .. note::

      We are using `BrowserID <http://browserid.org>`_, so a valid
      email address is required for your admin account.


#. **Update product_details package.**

   Package `product_details` provides information about countries. We
   use it in country selection lists. The information get pulled form
   mozilla's SVN, so we need to fetch it at least once. To update run::

     (venv)$ ./manage.py update_product_details


#. **Collect static files.**

   Various packages provide static files. We need to collect them in
   the STATIC_DIR::

     (venv)$ ./manage.py collectstatic


#. **Load demo data (optional).**

   Depending on what you are going to develop you may need to have
   some demo data.

   To load *demo users* run (within your VM)::

     (venv)$ ./manage.py loaddata demo_users

   To load *demo reports* run::

     (venv)$ ./manage.py loaddata demo_reports

   To load *demo events* run::

     (venv)$ ./manage.py loaddata demo_events

   To fetch *bugzilla bugs* run::

     (venv)$ ./manage.py fetch_bugs

   .. note::

      Fetching bugzilla bug requires a Mozilla Reps Admin account on
      Bugzilla. Ping `giorgos` on #remo-dev to give you access if
      your project requires it.
