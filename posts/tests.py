from __future__ import annotations

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from django.contrib.auth import get_user_model

from .models import Post


class PostFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="author",
            email="author@example.com",
            password="Passw0rd!123",
        )
        self.other_user = get_user_model().objects.create_user(
            username="viewer",
            email="viewer@example.com",
            password="Passw0rd!123",
        )
        self.post = Post.objects.create(
            author=self.user,
            title="First Post",
            content="Hello world",
            created_at=timezone.now(),
        )

    def test_post_create(self):
        self.client.login(username="author", password="Passw0rd!123")
        response = self.client.post(
            reverse("posts:create"),
            {
                "title": "Created Post",
                "content": "Created content",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Post.objects.filter(title="Created Post").exists())

    def test_post_update_only_author(self):
        self.client.login(username="author", password="Passw0rd!123")
        response = self.client.post(
            reverse("posts:update", args=[self.post.pk]),
            {"title": "Updated Post", "content": "Updated content"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Post.objects.get(pk=self.post.pk).title,
            "Updated Post",
        )

        self.client.login(username="viewer", password="Passw0rd!123")
        response = self.client.post(
            reverse("posts:update", args=[self.post.pk]),
            {"title": "Hack", "content": "hack"},
            follow=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Post.objects.get(pk=self.post.pk).title, "Updated Post")

    def test_post_delete_soft(self):
        self.client.login(username="author", password="Passw0rd!123")
        response = self.client.post(
            reverse("posts:delete", args=[self.post.pk]),
            follow=True,
        )
        self.assertRedirects(response, reverse("posts:list"))
        post = Post.objects.get(pk=self.post.pk)
        self.assertTrue(post.is_deleted)

    def test_view_count_increases(self):
        url = reverse("posts:detail", args=[self.post.pk])
        self.client.get(url)
        self.assertEqual(Post.objects.get(pk=self.post.pk).view_count, 1)
