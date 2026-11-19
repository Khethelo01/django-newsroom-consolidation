"""Persist role-aware users, publishers, reporting and delivery status.

Relationships are normalised with foreign keys and many-to-many tables.
Role-aware User properties return None where a relationship is inapplicable.
"""

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    """An authenticated account with reader, editor or journalist workflow.

    Reader subscriptions are stored separately from publisher staff membership.
    Save signals synchronise the role with the corresponding Django group.
    """

    role = models.CharField(
        max_length=12,
        choices=[
            ("reader", "Reader"),
            ("editor", "Editor"),
            ("journalist", "Journalist"),
        ],
        default="reader",
    )
    publisher_subscriptions = models.ManyToManyField(
        "Publisher", blank=True, related_name="subscribers"
    )
    journalist_subscriptions = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="subscribers",
        limit_choices_to={"role": "journalist"},
    )

    @property
    def reader_subscriptions(self):
        """Return publisher/journalist querysets for readers, else None.

        :return: Two lazy subscription querysets, or None for other roles.
        :rtype: tuple or None
        """
        if self.role != "reader":
            return None
        return (
            self.publisher_subscriptions.all(),
            self.journalist_subscriptions.all(),
        )

    @property
    def independent_articles(self):
        """Return this journalist's publisher-free articles, else None.

        :return: A lazy Article queryset for journalists, otherwise None.
        :rtype: django.db.models.QuerySet or None
        """
        return (
            self.articles.filter(publisher__isnull=True)
            if self.role == "journalist"
            else None
        )

    @property
    def independent_newsletters(self):
        """Return publisher-free newsletters for journalists, else None.

        :return: A lazy Newsletter queryset, or None for other roles.
        :rtype: django.db.models.QuerySet or None
        """
        return (
            self.newsletters.filter(publisher__isnull=True)
            if self.role == "journalist"
            else None
        )


class Publisher(models.Model):
    """A publishing organisation with editor and journalist memberships."""

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    editors = models.ManyToManyField(
        User,
        blank=True,
        related_name="edited_publishers",
        limit_choices_to={"role": "editor"},
    )
    journalists = models.ManyToManyField(
        User,
        blank=True,
        related_name="publishers",
        limit_choices_to={"role": "journalist"},
    )

    def __str__(self):
        """Return the display name for this record."""
        return self.name


class Article(models.Model):
    """Reporting that remains a draft until an editor approves it."""

    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="articles",
        limit_choices_to={"role": "journalist"},
    )
    publisher = models.ForeignKey(
        Publisher,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="articles",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    class Meta:
        """Configure the model ordering or form and serializer fields."""

        ordering = ["-created_at", "-pk"]

    def clean(self):
        """Validate journalist authorship and publisher membership."""
        if self.author_id and self.author.role != "journalist":
            raise ValidationError("Articles must have a journalist author.")
        if (
            self.publisher_id
            and not self.publisher.journalists.filter(
                pk=self.author_id
            ).exists()
        ):
            raise ValidationError("The author must belong to this publisher.")

    def __str__(self):
        """Return the display name for this record."""
        return self.title


class Newsletter(models.Model):
    """Newsletter for the News application."""

    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="newsletters"
    )
    publisher = models.ForeignKey(
        Publisher, on_delete=models.PROTECT, null=True, blank=True
    )
    articles = models.ManyToManyField(
        Article, blank=True, related_name="newsletters"
    )

    def __str__(self):
        """Return the display name for this record."""
        return self.title


class PublicationDelivery(models.Model):
    """Record email/API completion and the latest delivery error per article."""

    article = models.OneToOneField(
        Article, on_delete=models.CASCADE, related_name="delivery"
    )
    email_sent = models.BooleanField(default=False)
    api_sent = models.BooleanField(default=False)
    last_error = models.TextField(blank=True)


class ApprovalLog(models.Model):
    """Record an approved article received through the integration API."""

    article = models.OneToOneField(Article, on_delete=models.CASCADE)
    logged_at = models.DateTimeField(auto_now_add=True)
