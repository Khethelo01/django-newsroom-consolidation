"""Apps for the News application."""

from django.apps import AppConfig


class NewsConfig(AppConfig):
    """Newsconfig for the News application."""

    name = "news"

    def ready(self):
        """Ready for the News application."""
        from . import signals  # noqa: F401
