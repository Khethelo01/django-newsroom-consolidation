"""Api for the News application."""

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Article, Newsletter, ApprovalLog, Publisher
from .policies import is_editor, can_edit, subscribed_articles
from .serializers import (
    ArticleSerializer,
    NewsletterSerializer,
    PublisherSerializer,
)
from .services import approve_article


@api_view(["GET", "POST"])
def articles(request):
    """Articles for the News application."""
    if request.method == "GET":
        return Response(
            ArticleSerializer(
                Article.objects.filter(approved=True), many=True
            ).data
        )
    if request.user.role != "journalist":
        return Response({"detail": "Journalists only."}, status=403)
    serializer = ArticleSerializer(
        data=request.data, context={"request": request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save(author=request.user, approved=False)
    return Response(serializer.data, status=201)


@api_view(["GET"])
def subscribed(request):
    """Subscribed for the News application."""
    if request.user.role != "reader":
        return Response({"detail": "Readers only."}, status=403)
    return Response(
        ArticleSerializer(subscribed_articles(request.user), many=True).data
    )


@api_view(["GET", "PUT", "DELETE"])
def article_detail(request, pk):
    """Article detail for the News application."""
    article = get_object_or_404(Article, pk=pk)
    if request.method == "GET":
        if not article.approved and not can_edit(request.user, article):
            return Response({"detail": "Not found."}, status=404)
        return Response(ArticleSerializer(article).data)
    if not can_edit(request.user, article):
        return Response({"detail": "Permission denied."}, status=403)
    if request.method == "DELETE":
        article.delete()
        return Response(status=204)
    serializer = ArticleSerializer(
        article, data=request.data, context={"request": request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save(approved=False)
    from .models import PublicationDelivery

    PublicationDelivery.objects.filter(article=article).delete()
    ApprovalLog.objects.filter(article=article).delete()
    return Response(serializer.data)


@api_view(["POST"])
def approve(request, pk):
    """Approve for the News application."""
    if not is_editor(request.user):
        return Response({"detail": "Editors only."}, status=403)
    article = get_object_or_404(Article, pk=pk)
    approve_article(article, request.user)
    article.refresh_from_db()
    return Response(ArticleSerializer(article).data)


@api_view(["POST"])
def approved_log(request):
    """Approved log for the News application."""
    if not is_editor(request.user):
        return Response({"detail": "Editors only."}, status=403)
    article_id = request.data.get("article")
    if not str(article_id).isdecimal():
        return Response(
            {"detail": "A numeric article ID is required."}, status=400
        )
    article = get_object_or_404(Article, pk=article_id, approved=True)
    log, created = ApprovalLog.objects.get_or_create(article=article)
    return Response(
        {"id": log.pk, "article": article.pk}, status=201 if created else 200
    )


@api_view(["GET", "POST"])
def newsletters(request):
    """Newsletters for the News application."""
    if request.method == "GET":
        return Response(
            NewsletterSerializer(Newsletter.objects.all(), many=True).data
        )
    if request.user.role not in {"journalist", "editor"} and not is_editor(
        request.user
    ):
        return Response({"detail": "Permission denied."}, status=403)
    serializer = NewsletterSerializer(
        data=request.data, context={"request": request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save(author=request.user)
    return Response(serializer.data, status=201)


@api_view(["GET", "PUT", "DELETE"])
def newsletter_detail(request, pk):
    """Newsletter detail for the News application."""
    newsletter = get_object_or_404(Newsletter, pk=pk)
    if request.method == "GET":
        return Response(NewsletterSerializer(newsletter).data)
    if not (
        is_editor(request.user)
        or (
            request.user.role == "journalist"
            and newsletter.author_id == request.user.pk
        )
    ):
        return Response({"detail": "Permission denied."}, status=403)
    if request.method == "DELETE":
        newsletter.delete()
        return Response(status=204)
    serializer = NewsletterSerializer(
        newsletter, data=request.data, context={"request": request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["GET"])
def publishers(request):
    """Publishers for the News application."""
    return Response(
        PublisherSerializer(Publisher.objects.all(), many=True).data
    )
