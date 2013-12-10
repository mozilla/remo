==============================
Fire up the development server
==============================

These are the steps to run locally your development server.

Vagrant Installation
--------------------

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

VirtualEnv Installation
-----------------------

#. **Start django devserver.**

   Within your virtual environment you can start django devserver by
   running::

     (venv)$ ./manage.py runserver


#. **Visit our local installation of the ReMo Portal.**

   You are done! Point Firefox to `<http://127.0.0.1:8000>`_.
