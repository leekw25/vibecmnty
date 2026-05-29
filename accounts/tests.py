from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from io import BytesIO
from PIL import Image

from django.contrib.auth import get_user_model


class AuthFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_password = "Passw0rd!123"
        self.user = get_user_model().objects.create_user(
            username="member",
            email="member@example.com",
            password=self.user_password,
            role=get_user_model().Role.USER,
        )

    def test_signup_redirects_to_profile_and_logs_in(self):
        payload = {
            "username": "newmember",
            "email": "newmember@example.com",
            "password1": "Str0ngPass!234",
            "password2": "Str0ngPass!234",
        }

        response = self.client.post(reverse("accounts:signup"), payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("accounts:profile"), status_code=302, target_status_code=200)
        self.assertIn("_auth_user_id", self.client.session)

        user = get_user_model().objects.get(username="newmember")
        self.assertEqual(user.role, get_user_model().Role.USER)

    def test_profile_update_saves_avatar_and_fields(self):
        self.client.login(username="member", password=self.user_password)

        image_stream = BytesIO()
        Image.new("RGB", (1, 1), color="blue").save(image_stream, format="PNG")
        avatar = SimpleUploadedFile(
            "avatar.png", image_stream.getvalue(), content_type="image/png"
        )
        payload = {
            "display_name": "New Name",
            "bio": "Hello there",
            "first_name": "Test",
            "last_name": "User",
        }

        response = self.client.post(
            reverse("accounts:profile_edit"),
            {**payload, "avatar": avatar},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("accounts:profile"), status_code=302, target_status_code=200)

        user = get_user_model().objects.get(username="member")
        self.assertEqual(user.display_name, "New Name")
        self.assertTrue(bool(user.avatar))

    def test_password_change_updates_password(self):
        self.client.login(username="member", password=self.user_password)

        response = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": self.user_password,
                "new_password1": "N3wPass!456",
                "new_password2": "N3wPass!456",
            },
            follow=True,
        )
        self.assertRedirects(response, reverse("accounts:profile"), status_code=302, target_status_code=200)
        self.client.logout()
        assert self.client.login(username="member", password="N3wPass!456")

    def test_admin_access_denied_for_non_admin(self):
        self.client.login(username="member", password=self.user_password)
        response = self.client.get(reverse("admin_dashboard:home"))
        self.assertRedirects(
            response,
            reverse("home"),
            status_code=302,
            target_status_code=200,
        )
