"""Exercise role registration and front-end publisher management."""

from django.test import TestCase
from .forms import PublisherForm
from .models import User, Publisher


class ReviewWorkflowTests(TestCase):
    """Verify assessor-requested workflows without admin-panel access."""

    def setUp(self):
        """Create independent role accounts and an editorial team."""
        self.editor = User.objects.create_user("revieweditor", role="editor")
        self.other = User.objects.create_user("reviewother", role="editor")
        self.writer = User.objects.create_user(
            "reviewwriter", role="journalist"
        )
        self.reader = User.objects.create_user("reviewreader", role="reader")
        self.publisher = Publisher.objects.create(name="Existing publication")
        self.publisher.editors.add(self.editor)

    def test_registration_assigns_each_role_group_and_permissions(self):
        """Assign the selected role and matching group at sign-up."""
        for role in ["reader", "editor", "journalist"]:
            self.client.logout()
            response = self.client.post(
                "/register/",
                {
                    "username": "signup_" + role,
                    "email": role + "@example.com",
                    "role": role,
                    "password1": "DistinctPassword!234",
                    "password2": "DistinctPassword!234",
                },
            )
            self.assertEqual(response.status_code, 302)
            user = User.objects.get(username="signup_" + role)
            self.assertEqual(user.role, role)
            self.assertTrue(user.groups.filter(name=role.title()).exists())
            self.assertTrue(user.has_perm("news.view_article"))

    def test_invalid_registration_role_is_rejected(self):
        """Reject a crafted role value rather than granting privileges."""
        response = self.client.post(
            "/register/",
            {
                "username": "invalidrole",
                "role": "superuser",
                "password1": "DistinctPassword!234",
                "password2": "DistinctPassword!234",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="invalidrole").exists())

    def test_editor_creates_publisher_and_assigns_members(self):
        """Create a publisher through the normal web interface."""
        self.client.force_login(self.editor)
        response = self.client.post(
            "/publishers/new/",
            {
                "name": "New publication",
                "description": "Community reporting",
                "editors": [self.editor.pk],
                "journalists": [self.writer.pk],
            },
        )
        self.assertEqual(response.status_code, 302)
        publisher = Publisher.objects.get(name="New publication")
        self.assertTrue(publisher.editors.filter(pk=self.editor.pk).exists())
        self.assertTrue(
            publisher.journalists.filter(pk=self.writer.pk).exists()
        )

    def test_assigned_editor_updates_membership(self):
        """Allow the assigned editor to update publisher details."""
        self.client.force_login(self.editor)
        response = self.client.post(
            f"/publishers/{self.publisher.pk}/edit/",
            {
                "name": "Updated publication",
                "description": "New description",
                "editors": [self.editor.pk, self.other.pk],
                "journalists": [self.writer.pk],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.publisher.refresh_from_db()
        self.assertEqual(self.publisher.name, "Updated publication")
        self.assertEqual(self.publisher.editors.count(), 2)

    def test_unassigned_editor_cannot_manage_publisher(self):
        """Protect a publisher against unrelated editor accounts."""
        self.client.force_login(self.other)
        self.assertEqual(
            self.client.post(
                f"/publishers/{self.publisher.pk}/edit/", {}
            ).status_code,
            403,
        )

    def test_non_editors_cannot_create_publishers(self):
        """Deny publisher writes while allowing authenticated browsing."""
        for user in [self.writer, self.reader]:
            self.client.force_login(user)
            self.assertEqual(
                self.client.post("/publishers/new/", {}).status_code, 403
            )
            self.assertContains(
                self.client.get("/publishers/"), "Existing publication"
            )

    def test_member_choices_and_retained_manager(self):
        """Reject invalid member roles and self-removal from management."""
        form = PublisherForm(
            data={"name": "Invalid", "editors": [self.reader.pk]},
            manager=self.editor,
        )
        self.assertFalse(form.is_valid())
        form = PublisherForm(
            data={"name": "Invalid", "editors": [self.other.pk]},
            manager=self.editor,
        )
        self.assertFalse(form.is_valid())

    def test_anonymous_publisher_management_requires_login(self):
        """Redirect anonymous management requests to login."""
        self.assertEqual(self.client.get("/publishers/new/").status_code, 302)
