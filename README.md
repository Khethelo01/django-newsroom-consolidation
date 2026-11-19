# Newsroom - Consolidation Capstone

Khethelo Ntsele's final Django News capstone, extended with Git branch history,
Sphinx documentation and a working Docker/MariaDB stack.

Readers subscribe to publishers and independent journalists. Journalists write
articles and newsletters; editors manage publishers and approve reporting.
Approval attempts subscriber email and an authenticated API callback, recording
delivery outcomes. Role selection and publisher management use normal web pages.

## Quick start with Docker

Install Docker Desktop from https://www.docker.com/products/docker-desktop/
and complete its setup yourself. Start it and wait for the Linux container engine.
Windows may need WSL 2 and a restart. On Linux, Docker Engine and the Compose
plugin are sufficient. Then open PowerShell and run:

```powershell
git clone https://github.com/Khethelo01/django-newsroom-consolidation.git
cd django-newsroom-consolidation
Copy-Item .env.docker.example .env
notepad .env
```

In **Notepad**, replace `DJANGO_SECRET_KEY`, `DB_PASSWORD` and `DB_ROOT_PASSWORD`
with three different long random values. Docker reads this root `.env` file.
You can generate each value locally in PowerShell:

```powershell
$randomBytes = New-Object byte[] 32
$randomSource = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$randomSource.GetBytes($randomBytes)
([BitConverter]::ToString($randomBytes)).Replace('-', '').ToLowerInvariant()
$randomSource.Dispose()
```

Run that block three times and copy each result into the corresponding `.env`
entry. Save and close Notepad. These are your local secrets; never upload `.env`.
This project needs no Docker Hub account or access token to build locally.

```powershell
docker compose config --quiet
docker compose up --build -d --wait --wait-timeout 240
docker compose ps
```

Open **http://localhost:8000**. Register separate Reader, Journalist and Editor
accounts to try the workflows. There are no preconfigured accounts or passwords.
MariaDB is created automatically, migrations run at startup, and WhiteNoise serves
the collected CSS through Gunicorn. The app runs as a non-root account. Database
port 3306 is only on the Compose network; only web port 8000 is mapped to loopback.
If port 8000 is occupied, set `WEB_PORT=8001` in `.env` and open localhost:8001.

Optional administrator account:

```powershell
docker compose exec web python manage.py createsuperuser
```

Inspect or stop the stack:

```powershell
docker compose logs --tail 100 web
docker compose down
```

Stopping preserves the named database volume. Do not remove the volume unless
you intend to erase its data. Changing passwords in `.env` does not change an
already-initialised MariaDB account; keep the original values for that volume or
change the database password using MariaDB administration before changing `.env`.

## Run with a virtual environment (Windows PowerShell)

Use Python **3.13 or newer** for the pinned Sphinx version. The same project can
run without Docker using a locally installed MariaDB server.

```powershell
git clone https://github.com/Khethelo01/django-newsroom-consolidation.git
cd django-newsroom-consolidation
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item newsroom\.env.example newsroom\.env
notepad newsroom\.env
```

These commands call the virtual environment directly, so PowerShell activation
is unnecessary. In **Notepad**, generate and enter a new `DJANGO_SECRET_KEY`,
set `DB_ENGINE=mariadb`, and enter your database settings:

```text
DB_NAME=newsroom
DB_USER=newsroom_app
DB_PASSWORD=your-own-database-password
DB_HOST=127.0.0.1
DB_PORT=3306
DJANGO_DEBUG=1
APPROVAL_API_URL=http://127.0.0.1:8000/api/approved/
```

The Django app reads **newsroom/.env**; Compose instead reads the repository-root
**.env**. Use your server's actual port if it differs from 3306. If MariaDB is
not installed, install it from https://mariadb.org/download/ and set your own
root password during setup. On Windows, the following installs the official
package, then finds its command-line client:

```powershell
winget install --id MariaDB.Server --exact
$mariaClient = Get-ChildItem 'C:\Program Files\MariaDB*\bin\mariadb.exe' | Select-Object -First 1 -ExpandProperty FullName
& $mariaClient -u root -p
```

At the MariaDB prompt, run these SQL statements. Replace `YOUR_DATABASE_PASSWORD`
with the **same** password saved in `newsroom/.env`:

```sql
CREATE DATABASE newsroom CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'newsroom_app'@'127.0.0.1' IDENTIFIED BY 'YOUR_DATABASE_PASSWORD';
GRANT ALL PRIVILEGES ON newsroom.* TO 'newsroom_app'@'127.0.0.1';
GRANT ALL PRIVILEGES ON test_newsroom.* TO 'newsroom_app'@'127.0.0.1';
EXIT;
```

The `test_newsroom` grant lets Django create and remove its separate test database.
Now run these commands back in **PowerShell**, from the repository root:

```powershell
.\.venv\Scripts\python.exe newsroom\manage.py migrate
.\.venv\Scripts\python.exe newsroom\manage.py collectstatic --noinput
.\.venv\Scripts\python.exe newsroom\manage.py check
.\.venv\Scripts\python.exe newsroom\manage.py runserver 127.0.0.1:8000
```

Open http://localhost:8000. The development server is for local use. For a quick
SQLite-only demonstration, explicitly set `DB_ENGINE=sqlite` in `newsroom/.env`
and run migrations again; MariaDB remains the default and the verified Docker
deployment uses MariaDB. SQLite and MariaDB store separate databases.

On Linux/macOS, use `python3 -m venv .venv` and `.venv/bin/python` instead of
`.\.venv\Scripts\python.exe`; copy the example with `cp`. Installing mysqlclient
may require a compiler, pkg-config and MariaDB client development headers.

## Generate Sphinx documentation

The built documentation is already committed. Open
`newsroom/docs/_build/html/index.html` directly after cloning or extracting.

To regenerate it from the repository root:

```powershell
.\.venv\Scripts\python.exe -m sphinx -M clean newsroom/docs newsroom/docs/_build
.\.venv\Scripts\python.exe -m sphinx -M html newsroom/docs newsroom/docs/_build -W --keep-going
```

The configuration sets `DJANGO_SETTINGS_MODULE=config.settings` and calls
`django.setup()` before autodoc imports models. It forces SQLite for documentation
imports only and does not connect to the runtime database. The user guide explains
browser workflows; the API reference documents models, policies and delivery.
Source links are generated by viewcode. Cache files are ignored; HTML is tracked
as the explicit exception requested by this capstone brief.

## Verification

```powershell
.\.venv\Scripts\python.exe newsroom\manage.py test news --noinput
.\.venv\Scripts\python.exe -m flake8 --config newsroom/.flake8 newsroom/news newsroom/config
```

Verified run: https://github.com/Khethelo01/django-newsroom-consolidation/actions/runs/44535419207

The local regression suite passed all 33 tests; lint and the warning-as-error
Sphinx build passed. The intentional mocked offline-delivery test logs a timeout
while checking error recording; the suite still finishes with OK.

GitHub Actions builds the actual Docker image on a separate Linux machine,
starts MariaDB and Gunicorn, checks migrations, runs the capstone tests against
MariaDB, and exercises real HTTP registration, publisher management, article
creation, subscriptions, approval, delivery and API access. It creates random
disposable CI credentials; no account secrets are required for those tests.

The supplied brief suggests Docker Playground as an alternative remote machine.
https://labs.play-with-docker.com/ reports that it became unavailable on
1 March 2026. This project instead runs the Docker stack on GitHub-hosted Linux.

## Git workflow evidence

`docs` and `container` branch from the initial main commit. The docs branch
contains individual commits for models.py, policies.py and services.py before
the Sphinx build commit. The container branch introduces the Docker stack.
Both branches are merged into main with merge commits. This README sits in the
Django project's parent directory and is committed after those merges.

```powershell
git log --all --graph --oneline --decorate
git log docs -- newsroom/news/models.py newsroom/news/policies.py newsroom/news/services.py
```

## Credentials and limits

- Generate local database and Django secrets yourself; only example files are
  committed. The app refuses to start with debug disabled and no secret key.
- Console email is the default. For real delivery, acquire SMTP credentials from
  your provider and configure `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`,
  `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` and TLS in the private application
  environment. Never commit SMTP passwords, API tokens or reset links.
- Users choose editorial roles during coursework registration. A production
  service should gate editor access, enable HTTPS and add operational hardening.
- Approval uses synchronous delivery with recorded retry state, not a durable
  queue. Partial email failure may repeat some recipients on retry.

Submit `capstone.txt` separately at the task-folder root so the reviewer can
open the public repository immediately. The ZIP is an additional portable copy.
