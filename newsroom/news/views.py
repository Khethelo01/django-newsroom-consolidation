"""Views for the News application."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .models import Article, Newsletter
from .forms import RegisterForm, ArticleForm, NewsletterForm, SubscriptionForm
from .policies import is_editor, can_edit, visible_articles
from .services import approve_article


def home(request):
    """Home for the News application."""
    return render(
        request,
        "news/home.html",
        {"articles": Article.objects.filter(approved=True)},
    )


def register(request):
    """Register for the News application."""
    form = RegisterForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("home")
    return render(
        request,
        "form.html",
        {"form": form, "title": "Register and choose your role"},
    )


@login_required
def dashboard(request):
    """Dashboard for the News application."""
    return render(
        request,
        "news/dashboard.html",
        {
            "articles": visible_articles(request.user),
            "newsletters": Newsletter.objects.all(),
            "editor": is_editor(request.user),
        },
    )


@login_required
def article_detail(request, pk):
    """Article detail for the News application."""
    article = get_object_or_404(visible_articles(request.user), pk=pk)
    return render(
        request,
        "news/article.html",
        {
            "article": article,
            "editable": can_edit(request.user, article),
            "editor": is_editor(request.user),
        },
    )


@login_required
def article_edit(request, pk=None):
    """Article edit for the News application."""
    article = get_object_or_404(Article, pk=pk) if pk else None
    if (article and not can_edit(request.user, article)) or (
        not article and request.user.role != "journalist"
    ):
        return HttpResponseForbidden()
    author = article.author if article else request.user
    form = ArticleForm(
        request.POST if request.method == "POST" else None,
        instance=article,
        author=author,
    )
    if request.method == "POST" and form.is_valid():
        article = form.save(commit=False)
        article.approved = False
        article.save()
        from .models import PublicationDelivery, ApprovalLog

        PublicationDelivery.objects.filter(article=article).delete()
        ApprovalLog.objects.filter(article=article).delete()
        return redirect("dashboard")
    return render(
        request, "form.html", {"form": form, "title": "Write / edit article"}
    )


@login_required
@require_POST
def approve(request, pk):
    """Approve for the News application."""
    if not is_editor(request.user):
        return HttpResponseForbidden()
    approve_article(get_object_or_404(Article, pk=pk), request.user)
    messages.success(
        request, "Article approved. Delivery status is recorded for retry."
    )
    return redirect("dashboard")


@login_required
def article_delete(request, pk):
    """Article delete for the News application."""
    article = get_object_or_404(Article, pk=pk)
    if not can_edit(request.user, article):
        return HttpResponseForbidden()
    if request.method == "POST":
        article.delete()
        return redirect("dashboard")
    return render(request, "delete.html", {"object": article})


@login_required
def subscriptions(request):
    """Subscriptions for the News application."""
    if request.user.role != "reader":
        return HttpResponseForbidden()
    form = SubscriptionForm(
        request.POST if request.method == "POST" else None,
        instance=request.user,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Subscriptions updated.")
        return redirect("dashboard")
    return render(
        request, "form.html", {"form": form, "title": "Your subscriptions"}
    )


@login_required
def newsletter_detail(request, pk):
    """Newsletter detail for the News application."""
    newsletter = get_object_or_404(Newsletter, pk=pk)
    return render(request, "news/newsletter.html", {"newsletter": newsletter})


@login_required
def newsletter_edit(request, pk=None):
    """Newsletter edit for the News application."""
    obj = get_object_or_404(Newsletter, pk=pk) if pk else None
    allowed = is_editor(request.user) or (
        request.user.role == "journalist"
        and (obj is None or obj.author_id == request.user.pk)
    )
    if not allowed:
        return HttpResponseForbidden()
    form = NewsletterForm(
        request.POST if request.method == "POST" else None, instance=obj
    )
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        if not obj.pk:
            obj.author = request.user
        obj.save()
        form.save_m2m()
        return redirect("newsletter", pk=obj.pk)
    return render(
        request, "form.html", {"form": form, "title": "Curate newsletter"}
    )


@login_required
def newsletter_delete(request, pk):
    """Newsletter delete for the News application."""
    obj = get_object_or_404(Newsletter, pk=pk)
    if not (
        is_editor(request.user)
        or (
            request.user.role == "journalist"
            and obj.author_id == request.user.pk
        )
    ):
        return HttpResponseForbidden()
    if request.method == "POST":
        obj.delete()
        return redirect("dashboard")
    return render(request, "delete.html", {"object": obj})


@login_required
def publisher_list(request):
    """List publishers and link to membership-aware management pages."""
    from .models import Publisher

    return render(
        request,
        "news/publishers.html",
        {
            "publishers": Publisher.objects.all(),
            "editor": is_editor(request.user),
        },
    )


@login_required
def publisher_edit(request, pk=None):
    """Allow editors to create publishers or manage assigned publishers."""
    from .models import Publisher
    from .forms import PublisherForm

    if not is_editor(request.user):
        return HttpResponseForbidden("Only editors can manage publishers.")
    publisher = get_object_or_404(Publisher, pk=pk) if pk else None
    # Being an editor does not grant management of another editorial team.
    if publisher and not publisher.editors.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden(
            "You are not an editor for this publisher."
        )
    form = PublisherForm(
        request.POST if request.method == "POST" else None,
        instance=publisher,
        manager=request.user,
        initial={"editors": [request.user.pk]} if not publisher else None,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Publisher saved.")
        return redirect("publishers")
    return render(
        request, "form.html", {"form": form, "title": "Manage publisher"}
    )
