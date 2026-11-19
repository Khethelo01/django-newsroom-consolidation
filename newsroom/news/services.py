"""Services for the News application."""

import logging
import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from rest_framework.authtoken.models import Token
from .models import Article, PublicationDelivery, User

logger = logging.getLogger(__name__)


def approve_article(article, editor):
    """Commit editor approval before scheduling notification delivery."""
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
    """Deliver approval email and API logging with recorded retry state."""
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
