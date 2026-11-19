"""Policies for the News application."""

from django.db.models import Q
from .models import Article


def is_editor(user):
    """Recognise the editor role or explicit Editor group membership."""
    return user.role == "editor" or user.groups.filter(name="Editor").exists()


def can_edit(user, article):
    """Allow editors and the owning journalist to edit an article."""
    # A journalist may change their own reporting, never another author's.
    return is_editor(user) or (
        user.role == "journalist" and article.author_id == user.pk
    )


def subscribed_articles(user):
    """Return approved articles matching this reader subscriptions."""
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
    """Scope article visibility according to role and ownership."""
    if is_editor(user):
        return Article.objects.all()
    if user.role == "journalist":
        return Article.objects.filter(Q(approved=True) | Q(author=user))
    return Article.objects.filter(approved=True)
