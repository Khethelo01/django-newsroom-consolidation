Architecture and design decisions
=================================

Application layers
------------------

* ``news.models`` owns the normalised domain data and validation.
* ``news.forms`` validates browser input and role-filtered membership choices.
* ``news.policies`` scopes visibility, editing and subscription querysets.
* ``news.views`` handles authenticated HTML workflows.
* ``news.api`` and ``news.serializers`` expose authenticated JSON endpoints.
* ``news.services`` coordinates approval, email and integration delivery.
* ``news.signals`` synchronises role groups and constrains subscriptions.

Transactions and delivery
-------------------------

Approval locks the article row in an atomic transaction. Delivery is scheduled
with ``transaction.on_commit`` so the callback observes committed approval.
Email and API completion are recorded separately. This is synchronous delivery,
not a durable job queue. A partial email failure may repeat some recipients on
retry. A production design would use an outbox/worker and stronger idempotency.

The container runs Gunicorn with two workers and four threads each. Threads
allow the approval callback to be handled while the originating request waits
for it. The callback URL uses the container's own loopback address and port.
The callback checks authentication, approval and editor permission.

Role-aware data
---------------

Users select Reader, Editor or Journalist. Reader subscriptions, independent
articles and independent newsletters are exposed through role-aware properties
that return None when inapplicable. Many-to-many membership tables preserve
normalisation rather than duplicating role-specific fields.

Repository history
------------------

The initial commit imports the final capstone. The ``docs`` branch documents
models, policies and services in separate commits, then adds Sphinx sources and
built HTML. The ``container`` branch starts separately from the initial main
branch and adds Docker configuration. Both are merged into main, followed by
the setup README. Generated caches and secrets are ignored; documentation HTML
is the intentional exception requested by the brief.
