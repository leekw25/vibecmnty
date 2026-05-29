from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Event


class EventFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = get_user_model().objects.create_user(
            username="admin",
            email="admin@example.com",
            password="Passw0rd!123",
            role=get_user_model().Role.ADMIN,
        )
        self.user = get_user_model().objects.create_user(
            username="member",
            email="member@example.com",
            password="Passw0rd!123",
        )

    def _payload(self, title="Meeting"):
        start = timezone.now().replace(second=0, microsecond=0)
        end = start + timedelta(hours=1)
        return {
            "title": title,
            "description": "team sync",
            "category": "MEETING",
            "start_at": start.strftime("%Y-%m-%dT%H:%M"),
            "end_at": end.strftime("%Y-%m-%dT%H:%M"),
            "is_all_day": "on",
            "is_published": "on",
        }

    def test_event_create_requires_admin(self):
        self.client.login(username="member", password="Passw0rd!123")
        response = self.client.post(reverse("events:create"), self._payload(), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Event.objects.filter(title="Meeting").exists())

    def test_event_admin_create_update_delete(self):
        self.client.login(username="admin", password="Passw0rd!123")
        create = self.client.post(reverse("events:create"), self._payload("Admin Event"), follow=True)
        self.assertEqual(create.status_code, 200)
        self.assertTrue(Event.objects.filter(title="Admin Event").exists())

        event = Event.objects.get(title="Admin Event")
        update_payload = self._payload("Admin Event Updated")
        update_payload["is_all_day"] = ""
        update_payload["is_published"] = ""

        update = self.client.post(
            reverse("events:update", args=[event.pk]), update_payload, follow=True
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(
            Event.objects.get(pk=event.pk).title,
            "Admin Event Updated",
        )

        delete = self.client.post(
            reverse("events:delete", args=[event.pk]), follow=True
        )
        self.assertEqual(delete.status_code, 200)
        self.assertFalse(Event.objects.filter(pk=event.pk).exists())
