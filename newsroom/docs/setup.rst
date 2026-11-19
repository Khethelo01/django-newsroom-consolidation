Installation and operation
==========================

The repository-root README contains the full copy-and-paste commands for both
virtual-environment and Docker setup. It is the authoritative setup guide.

Virtual environment
-------------------

Clone the public repository, change into it, create a virtual environment,
install ``requirements-dev.txt``, and copy ``newsroom/.env.example`` to
``newsroom/.env``. Generate your own secret key and choose database credentials.
Install MariaDB, create a database and user as documented, then run migrations
and ``runserver`` from the ``newsroom`` directory.

The default Docker route creates MariaDB through Compose and needs no local
Python or MariaDB installation. A SQLite-only demonstration can be selected
explicitly in the environment for quick local inspection.

Docker
------

Copy ``.env.docker.example`` to ``.env`` at the repository root. Replace the
secret key, database password and database root password with independent
random values. Run ``docker compose up --build -d`` and open
http://localhost:8000. The database has a named volume and its healthcheck must
pass before the web container migrates and starts. The web app runs as a
non-root account and serves static files with WhiteNoise.

Stop the stack with ``docker compose down``. This preserves database storage.
Removing volumes destroys data, so it is not part of normal shutdown.

Documentation
-------------

From the repository root with build dependencies installed::

   python -m sphinx -b html newsroom/docs newsroom/docs/_build/html -W

Open ``newsroom/docs/_build/html/index.html``. The generated HTML is deliberately
tracked so visitors can read it without installing Sphinx. The configuration
sets ``DJANGO_SETTINGS_MODULE`` and calls ``django.setup()`` before autodoc
imports the models. Documentation uses a database-free SQLite configuration;
it does not need your MariaDB password or a running server.
