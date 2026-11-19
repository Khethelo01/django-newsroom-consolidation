"""Forms for the News application."""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Article, Newsletter, Publisher


class RegisterForm(UserCreationForm):
    """Registerform for the News application."""

    class Meta:
        """Configure the model ordering or form and serializer fields."""

        model = User
        fields = ["username", "email", "role", "password1", "password2"]


class PublisherForm(forms.ModelForm):
    """Edit publisher details and restrict membership to eligible roles."""

    class Meta:
        """Expose publisher information and editorial membership."""

        model = Publisher
        fields = ["name", "description", "editors", "journalists"]

    def __init__(self, *args, manager, **kwargs):
        """Scope membership choices and retain the managing editor."""
        super().__init__(*args, **kwargs)
        self.manager = manager
        self.fields["editors"].queryset = User.objects.filter(role="editor")
        self.fields["journalists"].queryset = User.objects.filter(
            role="journalist"
        )

    def clean_editors(self):
        """Prevent an editor from accidentally losing management access."""
        editors = self.cleaned_data["editors"]
        if not editors.filter(pk=self.manager.pk).exists():
            raise forms.ValidationError("Keep yourself selected as an editor.")
        return editors


class ArticleForm(forms.ModelForm):
    """Articleform for the News application."""

    class Meta:
        """Configure the model ordering or form and serializer fields."""

        model = Article
        fields = ["title", "content", "publisher"]

    def __init__(self, *args, author, **kwargs):
        """Initialise form fields and restrict their eligible model choices."""
        super().__init__(*args, **kwargs)
        self.instance.author = author
        self.fields["publisher"].queryset = Publisher.objects.filter(
            journalists=author
        )


class NewsletterForm(forms.ModelForm):
    """Newsletterform for the News application."""

    class Meta:
        """Configure the model ordering or form and serializer fields."""

        model = Newsletter
        fields = ["title", "description", "publisher", "articles"]

    def __init__(self, *args, **kwargs):
        """Initialise form fields and restrict their eligible model choices."""
        super().__init__(*args, **kwargs)
        self.fields["articles"].queryset = Article.objects.filter(
            approved=True
        )


class SubscriptionForm(forms.ModelForm):
    """Subscriptionform for the News application."""

    class Meta:
        """Configure the model ordering or form and serializer fields."""

        model = User
        fields = ["publisher_subscriptions", "journalist_subscriptions"]

    def __init__(self, *args, **kwargs):
        """Initialise form fields and restrict their eligible model choices."""
        super().__init__(*args, **kwargs)
        self.fields["journalist_subscriptions"].queryset = User.objects.filter(
            role="journalist"
        )
