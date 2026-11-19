User guide
==========

Getting started
---------------

After starting the application, visit http://localhost:8000. The public home
page lists approved articles. Select Register, enter a username and password,
and choose Reader, Journalist or Editor. Registration signs you in.

.. warning::

   Public editor registration is intentional for this coursework. A production
   deployment should require approval before granting editorial privileges.

Reader workflow
---------------

Open Subscriptions and select publishers or journalists. Save the form, then
use the subscribed-articles API to retrieve approved reporting matching those
subscriptions. The dashboard also lists reporting available to your role.
Publisher subscriptions include that organisation's approved articles;
journalist subscriptions select independent reporting by that journalist.

Journalist workflow
-------------------

Use Write article to enter a title and content. Choose one of your publishers
or leave it blank for independent reporting. A saved article is a draft. You
can edit your own articles. Editing an approved article resets its approval and
delivery records, so an editor must approve it again. You can also curate a
newsletter from the available articles.

Editor and publisher workflow
-----------------------------

Open Publishers and choose Create publisher. Enter its name and description,
select its editors and journalists, and save. The managing editor remains
assigned. An assigned editor can edit that publisher; other editors cannot
manage its membership. Editors can review, edit, approve and delete articles.

Approval attempts subscriber email and an authenticated approval-log callback.
The development email backend writes messages to the terminal/container logs;
it does not send real email. SMTP credentials are optional and private.
Delivery outcomes and errors are retained for inspection and retry.

Password reset
--------------

Use the login page's password-reset link with your registered email address.
With the console backend, the reset email appears in the application's logs.
Keep those logs private because reset links grant account access.

API usage
---------

Authenticated browser sessions or Django REST Framework tokens are accepted.
An account's token can be created by an administrator with::

   python manage.py drf_create_token USERNAME

Supply ``Authorization: Token YOUR_TOKEN`` with API requests. Keep the token
private. API routes include ``/api/articles/``, ``/api/articles/subscribed/``,
``/api/publishers/`` and ``/api/newsletters/``. Approval is an editor-only POST to
``/api/articles/ARTICLE_ID/approve/``. The ``/api/approved/`` callback records an
approved article using an editor's token.
