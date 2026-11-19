"""Urls for the News application."""

from django.urls import path
from . import views, api

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("publishers/", views.publisher_list, name="publishers"),
    path("publishers/new/", views.publisher_edit, name="publisher-create"),
    path(
        "publishers/<int:pk>/edit/",
        views.publisher_edit,
        name="publisher-edit",
    ),
    path("subscriptions/", views.subscriptions, name="subscriptions"),
    path("articles/new/", views.article_edit, name="article-create"),
    path("articles/<int:pk>/", views.article_detail, name="article"),
    path("articles/<int:pk>/edit/", views.article_edit, name="article-edit"),
    path(
        "articles/<int:pk>/delete/",
        views.article_delete,
        name="article-delete",
    ),
    path("articles/<int:pk>/approve/", views.approve, name="approve"),
    path("newsletters/new/", views.newsletter_edit, name="newsletter-create"),
    path("newsletters/<int:pk>/", views.newsletter_detail, name="newsletter"),
    path(
        "newsletters/<int:pk>/edit/",
        views.newsletter_edit,
        name="newsletter-edit",
    ),
    path(
        "newsletters/<int:pk>/delete/",
        views.newsletter_delete,
        name="newsletter-delete",
    ),
    path("api/articles/", api.articles, name="api-articles"),
    path("api/articles/subscribed/", api.subscribed, name="api-subscribed"),
    path("api/articles/<int:pk>/", api.article_detail, name="api-article"),
    path("api/articles/<int:pk>/approve/", api.approve, name="api-approve"),
    path("api/approved/", api.approved_log, name="api-approved"),
    path("api/newsletters/", api.newsletters, name="api-newsletters"),
    path(
        "api/newsletters/<int:pk>/",
        api.newsletter_detail,
        name="api-newsletter",
    ),
    path("api/publishers/", api.publishers, name="api-publishers"),
]
