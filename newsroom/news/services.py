"""Approve reporting transactionally and attempt external delivery.

Approval commits before delivery runs. Email and API outcomes are stored
independently so already-completed channels can be skipped on retry.
"""

import logging
import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from rest_framework.authtoken.models import Token
from .models import Article, PublicationDelivery, User

logger = logging.getLogger(__name__)


def approve_article(article, editor):
    """Commit editor approval before scheduling notification delivery.

    :param article: An existing article; its database row is locked.
    :type article: news.models.Article
    :param editor: The approving authenticated editor.
    :type editor: news.models.User
    :return: The approved article refreshed inside the transaction.
    :rtype: news.models.Article
    :raises PermissionError: If the account is not an editor.
    :raises news.models.Article.DoesNotExist: If the article was removed.
    """
    from .policies import is_editor

    if not is_editor(editor):
        raise PermissionError("Only editors can approve articles.")
    with transaction.atomic():
        article = Article.objects.select_for_update().get(pk=article.pk)
        article.approved = True
        article.save(update_fields=["approved"])
        PublicationDelivery.objects.get_or_create(article=article)
        # Deliver only after committed data is visible to the HTTP callback.
        transaction.on_commit(lambda: deliver_article(article.pk, editor.pk))
    return article


def deliver_article(article_id, editor_id):
    """Attempt email and API delivery, recording errors for later retry.

    An unapproved article is ignored. Delivery exceptions are recorded in
    PublicationDelivery.last_error. Database lookup errors still propagate.
    Email delivery can repeat some recipients after a partial batch failure.

    :param article_id: Primary key of the article to deliver.
    :type article_id: int
    :param editor_id: Account used to authenticate the approval callback.
    :type editor_id: int
    :return: No value; delivery state is persisted.
    :rtype: None
    :raises news.models.Article.DoesNotExist: If the article is absent.
    """
    article = Article.objects.get(pk=article_id)
    delivery, _ = PublicationDelivery.objects.get_or_create(article=article)
    if not article.approved:
        return
    if article.publisher_id:
        readers = User.objects.filter(
            role="reader", publisher_subscriptions=article.publisher
        )
    else:
        readers = User.objects.filter(
            role="reader", journalist_subscriptions=article.author
        )
    errors = []
    if not delivery.email_sent:
        emails = list(
            readers.exclude(email="")
            .values_list("email", flat=True)
            .distinct()
        )
        try:
            for email in emails:
                send_mail(
                    article.title,
                    article.content,
                    None,
                    [email],
                    fail_silently=False,
                )
            delivery.email_sent = True
        except Exception as error:
            logger.exception("Article email failed")
            errors.append(str(error))
    if not delivery.api_sent:
        try:
            token, _ = Token.objects.get_or_create(user_id=editor_id)
            response = requests.post(
                settings.APPROVAL_API_URL,
                json={"article": article.pk},
                headers={"Authorization": f"Token {token.key}"},
                timeout=5,
            )
            response.raise_for_status()
            delivery.api_sent = True
        except requests.RequestException as error:
            logger.exception("Approval integration failed")
            errors.append(str(error))
    delivery.last_error = "; ".join(errors)
    delivery.save()
