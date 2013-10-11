===================
Static files setup
===================

Installing LESS Preprocessor
-----------------------------

#. **Install Node.js** for vagrant users

   - Install prerequisites::

     ~$ sudo apt-get install g++ libssl-dev build-essential

   - Download latest `Node.js <http://nodejs.org/download/>`_
     source code (eg.)::

     ~$ wget http://nodejs.org/dist/v0.10.20/node-v0.10.20.tar.gz

   - Extract source code::

     ~$ tar -zxf node-v0.10.20.tar.gz

   - To build Node.js, run inside the extracted folder::

     ~$ ./configure
     ~$ make
     ~$ sudo make install

   .. note::

    For other development environments (eg. virtualenv), follow the Node.js
    `installation guide <https://github.com/joyent/node/wiki/Installation>`_
    or use your `package manager <https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager>`_
    if a package is available.

#. **Install lessc using npm**::

     ~$ sudo npm install -g less


Settings
--------

.. attribute:: COMPRESS_ENABLED

     If set to ``True`` django serves static files compressed.

.. attribute:: COMPRESS_OFFLINE

    If set to ``True`` static files will be compressed outside request/response
    loop. If set to ``False`` static files will be processed on user requests.
