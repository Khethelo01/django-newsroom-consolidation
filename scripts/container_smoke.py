"""Check real HTTP role workflows against the running container stack."""
import secrets
import requests
from news.models import ApprovalLog, Article, PublicationDelivery, User

BASE = "http://127.0.0.1:8000"
suffix = secrets.token_hex(4)
password = secrets.token_urlsafe(24)


def post_form(session, path, data):
    """Submit a CSRF-protected browser form using its actual cookie."""
    response = session.get(BASE + path, timeout=10)
    response.raise_for_status()
    return session.post(
        BASE + path,
        data=data,
        headers={"X-CSRFToken": session.cookies["csrftoken"]},
        timeout=20,
        allow_redirects=False,
    )


sessions = {}
users = {}
for role in ("reader", "editor", "journalist"):
    session = requests.Session()
    username = role + suffix
    response = post_form(session, "/register/", {
        "username": username,
        "email": username + "@example.test",
        "role": role,
        "password1": password,
        "password2": password,
    })
    assert response.status_code == 302, (role, response.status_code)
    user = User.objects.get(username=username)
    assert user.role == role and user.groups.filter(name=role.title()).exists()
    sessions[role] = session
    users[role] = user

response = post_form(sessions["editor"], "/publishers/new/", {
    "name": "Container verification " + suffix,
    "description": "Ephemeral CI publisher",
    "editors": [users["editor"].pk],
    "journalists": [users["journalist"].pk],
})
assert response.status_code == 302
publisher = users["editor"].edited_publishers.get(name__endswith=suffix)
response = post_form(sessions["journalist"], "/articles/new/", {
    "title": "Container article " + suffix,
    "content": "A report created through the real container HTTP interface.",
    "publisher": publisher.pk,
})
assert response.status_code == 302
article = Article.objects.get(title="Container article " + suffix)
assert not article.approved
response = post_form(sessions["reader"], "/subscriptions/", {
    "publisher_subscriptions": [publisher.pk],
})
assert response.status_code == 302
# Approval uses an actual HTTP callback handled by another Gunicorn thread.
session = sessions["editor"]
response = session.post(
    BASE + f"/articles/{article.pk}/approve/",
    headers={"X-CSRFToken": session.cookies["csrftoken"]},
    timeout=20,
    allow_redirects=False,
)
assert response.status_code == 302
article.refresh_from_db()
assert article.approved
delivery = PublicationDelivery.objects.get(article=article)
assert delivery.email_sent and delivery.api_sent, delivery.last_error
assert ApprovalLog.objects.filter(article=article).exists()
response = sessions["reader"].get(
    BASE + "/api/articles/subscribed/", timeout=10
)
response.raise_for_status()
assert any(item["id"] == article.pk for item in response.json())
response = requests.get(BASE + "/api/articles/", timeout=10)
assert response.status_code in (401, 403)
response = requests.get(BASE + "/static/news/style.css", timeout=10)
response.raise_for_status()
assert "text/css" in response.headers["Content-Type"]
print("PASS: role registration, group assignment and publisher management")
print("PASS: journalist draft, reader subscription and editor approval")
print("PASS: real email delivery state and authenticated API callback")
print("PASS: subscribed JSON API, anonymous denial and static CSS")
