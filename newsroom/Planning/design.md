# Newsroom design and interpretation

## Scope and requirements

Readers browse approved articles and newsletters and subscribe to publishers
or independent journalists. Journalists create articles, edit/delete their
own work and curate newsletters. Editors review drafts, edit/delete content,
approve articles and curate newsletters. Article creation remains journalist
only. Public registration exposes Reader, Editor and Journalist roles for this
coursework. Assigned editors manage publishers through front-end forms.

## Normalisation and role fields

Custom User extends AbstractUser and records role. Publisher stores publication
details. Editor and journalist memberships use separate many-to-many tables.
Article stores a title, content, author FK, optional publisher FK, creation time
and approval flag. A NULL publisher means independent journalism; a non-NULL
publisher requires author membership. Newsletter stores its own title,
description, creation time and author; article curation uses an M:N join table.
Reader subscriptions use separate publisher and journalist join tables.
These tables avoid repeating groups and maintain third-normal-form separation
of user, publisher, article and newsletter facts. Foreign keys enforce identity.

The brief asks for inapplicable user fields to be None. Django M:N relations
cannot be SQL NULL; their correct empty state is an empty join table. We expose
reader_subscriptions, independent_articles and independent_newsletters as
role-aware properties returning None when irrelevant, and prevent journalists
from adding reader subscriptions. Independent content is a filtered reverse
relation instead of a duplicated FK on User. This keeps the database normalised.

## Access control and endpoint meanings

GET /api/articles/ lists all approved content as explicitly requested.
GET /api/articles/subscribed/ is reader-only and strictly filters that reader's
subscriptions. A publisher subscription matches publisher content; a journalist
subscription matches independent articles by that journalist. Drafts never
appear in either feed. Journalists can inspect their own drafts; editors can
review all drafts. Only owners or editors edit/delete articles and newsletters.
Article authors and approval status are assigned server-side, not trusted from
JSON input. Editing an article returns it to the approval queue.

The brief's broad wording about readers retrieving subscribed content is
interpreted in the explicit subscribed endpoint; it does not silently change
the required all-approved endpoint into a subscription-only feed.

## Groups, API and security

Role assignment synchronises Reader, Editor or Journalist group membership.
Post-migration setup installs view permissions for Reader; view/change/delete
for Editor; add/view/change/delete for Journalist. Views and API additionally
enforce role and object ownership. Session auth serves the browser; DRF token
auth serves external API clients. POST /api/token/ is the login endpoint.
Article, User, Newsletter and Publisher all have DRF serializers. Sensitive user
fields are omitted. Authenticated editor access protects /api/approved/.

## Approval integration (Option 2: service called by approval view)

Approval commits the article and its delivery record before an on_commit
callback attempts email and requests.post to the application's own configured
/api/approved/ endpoint. The HTTP client sends an editor token and times out
after five seconds. The endpoint logs the approved article idempotently.
Email is delivered individually to avoid disclosing subscriber addresses.
Delivery flags and last_error record failures; the editor dashboard supports
retry. A successful retry skips already successful channels. No real email
leaves the machine under the default console backend. Concurrent callers and
partial multi-recipient SMTP failures would require a per-recipient outbox for
production-grade exactly-once delivery; this coursework implementation provides
recorded best-effort delivery and safe HTTP-log retries.

## UX and failure handling

Home prioritises published reporting. Reader dashboard links subscriptions;
journalist dashboard links writing/curation; editor dashboard exposes pending
approvals and delivery status. Forms display validation errors without losing
input. Deletes require a confirmation page and POST. Unknown objects return
404, missing authentication 401 (API), and forbidden actions 403. Layout adapts
to small screens with visible keyboard focus. Automated tests mock email and
HTTP integration and cover both successful and failed requests.

Review update: role self-selection and publisher management are available
through ordinary front-end forms. Publisher changes require assigned-editor
membership. Production should gate privileged role registration.
