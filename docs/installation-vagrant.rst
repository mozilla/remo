====================
Vagrant Installation
====================

Getting our own development environment.

Preparing Your System
---------------------

#. **Install Vagrant.**

   Vagrant is a manager of VMs for development. It streamlines and
   simplifies the procedure to get your own development environment
   for each project you are working on.

   Based on a configuration file, it creates Virtual Machines based on
   VirtualBox and configures folder and port sharing among your host
   machine and guest machine for easier access. It works nicely along
   with tools like puppet and automatically install and configures all
   the required programs and services (e.g. MySQL, Apache, etc) needed
   for development.

   This way all developers of a single project share the same
   environment.

   Most Linux distributions come with vagrant packaged, so probably
   you need to just install the package.

   - For Debian based systems::

     ~$ sudo apt-get install vagrant

   For other Linux distributions or operating systems visit `Vagrant's
   download page <http://downloads.vagrantup.com/>`_.


#. **Install git.**

   Our code is revisioned using `git <http://git-scm.org>`_. You can
   install it on your Linux machine through your package manager.

   - For Debian based systems::

     ~$ sudo apt-get install git

   For other Linux distributions or operating systems visit `Git's
   download page <http://git-scm.com/downloads>`_.



Build The Environment
---------------------

#. **Clone ReMo repository.**

   Mozilla Reps Portal is hosted on `<http://github.com/mozilla/remo>`_.

   Clone the repository locally::

     ~$ git clone --recursive http://github.com/mozilla/remo


   .. note::

      Make sure you use ``--recursive`` when checking the repo out!
      If you didn't, you can load all the submodules with ``git
      submodule update --init --recursive``.


#. **Fire up vagrant.**

   Now you need to build the virtual machine where ReMo portal will
   live. Change into the cloned directory and run vagrant::

     ~$ cd remo
     ~/remo$ vagrant up

   .. note::

      The first time you run vagrant an VM image will be downloaded
      and the guest machine will be configured. You will be
      downloading more than 300Mb. A (decent) internet connection is
      required.


#. **Connect to your vagrant machine.**

   You can connect to your vagrant machine, when it's running, using::

     ~/remo$ vagrant ssh


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


#. **Create an admin account.**

   Within your vagrant machine, create your own admin account::

    ~/project$ ./manage.py createsuperuser


   .. note::

      We are using `BrowserID <http://browserid.org>`_, so a valid
      email address is required for your admin account.


#. **Update product_details package.**

   Package `product_details` provides information about countries. We
   use it in country selection lists. The information get pulled form
   mozilla's SVN, so we need to fetch it at least once. To update run::

     ~/project$ ./manage.py update_product_details


#. **Collect static files.**

   Various packages provide static files. We need to collect them in
   the STATIC_DIR::

     ~/project$ ./manage.py collectstatic


#. **Load demo data (optional).**

   Depending on what you are going to develop you may need to have
   some demo data.

   To load *demo users* run (within your VM)::

     ~/project$ ./manage.py loaddata demo_users

   To load *demo reports* run::

     ~/project$ ./manage.py loaddata demo_reports

   To load *demo events* run::

     ~/project$ ./manage.py loaddata demo_events

   To fetch *bugzilla bugs* run::

     ~/project$ ./manage.py fetch_bugs

   .. note::

      Fetching bugzilla bug requires a Mozilla Reps Admin account on
      Bugzilla. Ping `giorgos` on #remo-dev to give you access if
      your project requires it.

#. **Start django devserver.**

   Within your vagrant machine you can start django devserver by
   running::

     $ cd project
     ~/project$ ./manage.py runserver 0.0.0.0:8000

   .. note::

      The `~/project` directory within the VM mirrors the contents of
      the `~/remo/` directory in you machine. So you can hack on your
      machine, using your favorite editor and your changes get
      reflected to the VM immediately.

   .. note::

      Since we are running the django webserver inside a VM it's
      required that bind the server on all network interfaces, so it's
      accessible from the host machine. Thus the use of *0.0.0.0:8000*
      in the command.

#. **Visit our local installation of the ReMo Portal.**

   You are done! Point Firefox to `<http://127.0.0.1:8000>`_.
