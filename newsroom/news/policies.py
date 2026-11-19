"""Centralise role, ownership and subscription query policies.

These helpers expect an authenticated news.models.User. Callers protect
private views with login_required or authenticated API permissions.
"""

from django.db.models import Q
from .models import Article


def is_editor(user):
    """Recognise the editor role or explicit Editor group membership.

    :param user: The authenticated account whose role is checked.
    :type user: news.models.User
    :return: Whether either editor check succeeds.
    :rtype: bool
    """
    return user.role == "editor" or user.groups.filter(name="Editor").exists()


def can_edit(user, article):
    """Allow editors and the owning journalist to edit an article.

    :param user: The authenticated account requesting a change.
    :type user: news.models.User
    :param article: The persisted article being changed.
    :type article: news.models.Article
    :return: True for an editor or the article's journalist author.
    :rtype: bool
    """
    # A journalist may change their own reporting, never another author's.
    return is_editor(user) or (
        user.role == "journalist" and article.author_id == user.pk
    )


def subscribed_articles(user):
    """Return approved articles matching this reader's subscriptions.

    Publisher subscriptions select their published articles; journalist
    subscriptions select independent articles. Duplicates are removed.

    :param user: The account whose subscriptions are evaluated.
    :type user: news.models.User
    :return: A lazy queryset, empty for non-reader accounts.
    :rtype: django.db.models.QuerySet
    """
    if user.role != "reader":
        return Article.objects.none()
    return (
        Article.objects.filter(approved=True)
        .filter(
            Q(publisher__in=user.publisher_subscriptions.all())
            | Q(
                publisher__isnull=True,
                author__in=user.journalist_subscriptions.all(),
            )
        )
        .distinct()
    )


def visible_articles(user):
    """Scope article visibility according to role and ownership.

    :param user: An authenticated account.
    :type user: news.models.User
    :return: All articles for editors; approved or owned articles for
        journalists; approved articles for readers.
    :rtype: django.db.models.QuerySet
    """
    if is_editor(user):
        return Article.objects.all()
    if user.role == "journalist":
        return Article.objects.filter(Q(approved=True) | Q(author=user))
    return Article.objects.filter(approved=True)
