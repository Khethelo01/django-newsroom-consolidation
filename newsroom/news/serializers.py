"""Serializers for the News application."""

from rest_framework import serializers
from .models import Article, User, Publisher, Newsletter


class UserSerializer(serializers.ModelSerializer):
    """Userserializer for the News application."""

    class Meta:
        """Configure the model ordering or form and serializer fields."""

        model = User
        fields = ["id", "username", "role"]


class PublisherSerializer(serializers.ModelSerializer):
    """Publisherserializer for the News application."""

    class Meta:
        """Configure the model ordering or form and serializer fields."""

        model = Publisher
        fields = ["id", "name", "description", "editors", "journalists"]


class ArticleSerializer(serializers.ModelSerializer):
    """Articleserializer for the News application."""

    class Meta:
        """Configure the model ordering or form and serializer fields."""

        model = Article
        fields = [
            "id",
            "title",
            "content",
            "author",
            "created_at",
            "approved",
            "publisher",
        ]
        read_only_fields = ["author", "created_at", "approved"]

    def validate(self, attrs):
        """Validate for the News application."""
        author = (
            self.instance.author
            if self.instance
            else self.context["request"].user
        )
        publisher = attrs.get(
            "publisher", self.instance.publisher if self.instance else None
        )
        if (
            publisher
            and not publisher.journalists.filter(pk=author.pk).exists()
        ):
            raise serializers.ValidationError(
                "Author must be a journalist for this publisher."
            )
        return attrs


class NewsletterSerializer(serializers.ModelSerializer):
    """Newsletterserializer for the News application."""

    def to_representation(self, instance):
        """To representation for the News application."""
        data = super().to_representation(instance)
        data["articles"] = list(
            instance.articles.filter(approved=True).values_list(
                "pk", flat=True
            )
        )
        return data

    class Meta:
        """Configure the model ordering or form and serializer fields."""

        model = Newsletter
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "author",
            "publisher",
            "articles",
        ]
        read_only_fields = ["created_at", "author"]

    def validate_articles(self, articles):
        """Validate articles for the News application."""
        if any(not article.approved for article in articles):
            raise serializers.ValidationError(
                "Only approved articles can be included."
            )
        return articles
