# Newsroom - Django assignment

## Setup

Use Python 3.10 or newer. This project was verified with Python 3.14. Extract
the archive before running commands. From the folder containing manage.py:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8022
```

If activation is blocked, replace python with `.\.venv\Scripts\python.exe`.
For macOS/Linux, use `source .venv/bin/activate`. mysqlclient may require the
platform's MariaDB/MySQL client development libraries and compiler. An SQLite
quick trial needs only requirements.txt. The capstone's required MariaDB setup
is described below and was actually performed, not merely configured.

## MariaDB

The local verification used MariaDB 13.0.2, port 3307, with an isolated,
password-protected instance and dedicated users. Credentials and database
files are not included. On another machine, create an utf8mb4 database and
a dedicated account, grant that account privileges on its own database and
on `test_newsroom` for Django's temporary test database, then set:

```powershell
$env:DB_ENGINE = "mariadb"
$env:DB_NAME = "newsroom"
$env:DB_USER = "YOUR_LOCAL_DATABASE_USER"
$env:DB_PASSWORD = "YOUR_LOCAL_DATABASE_PASSWORD"
$env:DB_HOST = "127.0.0.1"
$env:DB_PORT = "3307"
python manage.py migrate
python manage.py check --database default
python manage.py test news -v 2
```

The SQLite fallback is for easy preview. Keep DB_ENGINE=mariadb when reviewing
the actual capstone database. See mariadb_verification.txt for recorded migration
and test output. Migration files are included and must not be deleted.

## Accounts and email

No real credentials, private tokens or user databases are in the submission.
Register through /register/ and choose Reader, Editor or Journalist. The application uses Django
sessions for browser login. Optional admin is at /admin/ after createsuperuser.
Passwords use Django hashing and validation. Password recovery is at
/accounts/password_reset/ with a 15-minute, invalidated-after-use token.

Console email is the safe default: messages appear in the server terminal.
To use real SMTP, set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend,
EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_USE_TLS and
DEFAULT_FROM_EMAIL as environment variables. Do not commit real credentials.
No real recipients were emailed during verification.

## Tests and development checks

```text
python manage.py test news -v 2
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py collectstatic --noinput
python -m flake8 .
```

Tests use isolated databases; external HTTP and email failures are mocked.
The suite was run on both SQLite and MariaDB. Manual browser checks and live
integration results are recorded in verification.txt. CSS and templates work
without remote fonts or CDNs. Source is split into models, forms, views,
services, serializers, routing, policies where applicable, and tests.

## Planning and submission

Planning/design.md maps requirements to workflows, authorisation and data.
Planning/design_diagrams.pdf includes use case, sequence and class/relational
diagrams. requirements files pin runtime and development dependencies.
Generated databases, virtual environments, caches, static collection copies
and private configuration are excluded from the ZIP.

This is local coursework, not a deployed production service. Production needs
HTTPS, a private DJANGO_SECRET_KEY, DJANGO_DEBUG=0, approved hosts, suitable
deployment infrastructure, rate limiting and backups. Do not expose the
development server publicly.

## News roles and subscriptions

Public coursework registration lets users choose Reader, Editor or Journalist.
The post-save signal assigns the corresponding group and permissions. Role changes synchronise group
membership. The migrations configure appropriate model permissions per group;
views/API enforce role and ownership in addition to group membership.

Editors open Publishers > Create publisher, select themselves and their
editor/journalist team, then save. Assigned editors use Manage publisher to
update details or membership. Readers and journalists can browse publisher
teams but cannot change them. No superuser is required. Then use
Journalist dashboard to write articles or newsletters. Blank publisher means
independent reporting. Readers manage subscriptions through their dashboard.
Editor dashboard reviews drafts and approves publication. Edits require
reapproval. Approval uses Option 2: an explicit service from the approval view,
with on_commit delivery. The internal API receives a real requests.post call.

Start the server on port 8022, or set APPROVAL_API_URL to the matching
http://127.0.0.1:PORT/api/approved/ endpoint. The endpoint requires an editor
token, created server-side for the callback. Keep it on trusted local HTTPS
in production. Delivery errors are recorded and can be retried by an editor.

### API

POST /api/token/ authenticates credentials and returns a token. Include the
Authorization: Token YOUR_TOKEN header on subsequent requests.

| Route | Access and methods |
| --- | --- |
| /api/articles/ | GET approved articles; POST journalist-only drafts |
| /api/articles/subscribed/ | GET reader's subscribed approved content |
| /api/articles/ID/ | GET; PUT/DELETE owner journalist or editor |
| /api/articles/ID/approve/ | POST editor only |
| /api/approved/ | POST editor only; idempotent internal log |
| /api/newsletters/ | GET; POST journalist/editor |
| /api/newsletters/ID/ | GET; PUT/DELETE owner or editor |
| /api/publishers/ | GET authenticated clients |

All four required serializers (Article, User, Newsletter and Publisher) are
in news/serializers.py. User output excludes secrets and passwords. See
Planning/design.md for explicit interpretations of None on M:N fields and
the distinction between the all-approved and subscribed feeds.


## Review revision: configuration and front-end workflows

After cloning and installing requirements, run the following in PowerShell
from the project folder containing manage.py:

```powershell
Copy-Item .env.example .env
notepad .env
```

Replace the sample secret, database password, username, name and port with your
local MariaDB values, then save and close Notepad. python-dotenv loads this
file automatically. Existing shell variables take precedence. The real .env
is excluded from Git and submission archives. The supplied example selects
MariaDB; SQL setup and migration commands are documented above. Email defaults
to console output for local tests. Start on port 8022 to match the callback.

Registration now exposes the three requested roles. This intentionally allows
editor self-registration in the coursework; a public production deployment
should require approval or invitation for privileged roles. Editor accounts
can create publishers and assign members directly from Publishers, and only
assigned editors can manage an existing publisher. The form prevents accidental
removal of the managing editor. Publisher creation requires no admin access.
