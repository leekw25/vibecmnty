from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Poll, PollOption


class PollFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = get_user_model().objects.create_user(
            username="poll_admin",
            email="admin@poll.com",
            password="Passw0rd!123",
            role=get_user_model().Role.ADMIN,
        )
        self.user = get_user_model().objects.create_user(
            username="member",
            email="member@poll.com",
            password="Passw0rd!123",
        )

    def _payload(self, question="Week Poll"):
        end = (timezone.now().replace(second=0, microsecond=0) + timedelta(days=1))
        return {
            "question": question,
            "expires_at": end.strftime("%Y-%m-%dT%H:%M"),
            "options-TOTAL_FORMS": "2",
            "options-INITIAL_FORMS": "0",
            "options-MIN_NUM_FORMS": "2",
            "options-MAX_NUM_FORMS": "10",
            "options-0-text": "A",
            "options-1-text": "B",
        }

    def test_admin_can_create_poll(self):
        self.client.login(username="poll_admin", password="Passw0rd!123")
        response = self.client.post(
            reverse("polls:new"),
            self._payload("Admin Poll"),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        poll = Poll.objects.get(question="Admin Poll")
        self.assertEqual(poll.options.count(), 2)

    def test_user_cannot_create_poll(self):
        self.client.login(username="member", password="Passw0rd!123")
        response = self.client.post(
            reverse("polls:new"),
            self._payload("User Poll"),
            follow=False,
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Poll.objects.filter(question="User Poll").exists())

    def test_poll_list_shows_options_count(self):
        self.client.login(username="poll_admin", password="Passw0rd!123")
        self.client.post(reverse("polls:new"), self._payload("List Poll"), follow=True)
        response = self.client.get(reverse("polls:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "List Poll")

    def test_poll_can_be_voted_once(self):
        self.client.login(username="poll_admin", password="Passw0rd!123")
        self.client.post(reverse("polls:new"), self._payload("One Vote Poll"), follow=True)
        poll = Poll.objects.get(question="One Vote Poll")
        option = PollOption.objects.filter(poll=poll).first()
        self.client.logout()
        self.client.login(username="member", password="Passw0rd!123")
        response = self.client.post(
            reverse("polls:detail", args=(poll.pk,)),
            {"option": str(option.pk)},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "결과를 보여드립니다.")
