from unittest import mock

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class AuthApiTests(APITestCase):
    def test_register_creates_user_and_returns_tokens(self):
        response = self.client.post(
            reverse("auth-register"),
            {
                "username": "matan",
                "email": "matan@example.com",
                "password": "StrongPass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])
        self.assertTrue(get_user_model().objects.filter(username="matan").exists())

    def test_login_returns_tokens_for_existing_user(self):
        user_model = get_user_model()
        user_model.objects.create_user(
            username="matan",
            email="matan@example.com",
            password="StrongPass123",
        )

        response = self.client.post(
            reverse("auth-login"),
            {"username": "matan", "password": "StrongPass123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])

    def test_register_rejects_weak_password(self):
        response = self.client.post(
            reverse("auth-register"),
            {
                "username": "matan",
                "email": "matan@example.com",
                "password": "1234",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_login_rejects_invalid_credentials(self):
        user_model = get_user_model()
        user_model.objects.create_user(
            username="matan",
            email="matan@example.com",
            password="StrongPass123",
        )

        response = self.client.post(
            reverse("auth-login"),
            {"username": "matan", "password": "WrongPass"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_returns_new_access_token(self):
        user_model = get_user_model()
        user_model.objects.create_user(
            username="matan",
            email="matan@example.com",
            password="StrongPass123",
        )

        login_response = self.client.post(
            reverse("auth-login"),
            {"username": "matan", "password": "StrongPass123"},
            format="json",
        )
        refresh_token = login_response.data["tokens"]["refresh"]

        refresh_response = self.client.post(
            reverse("auth-refresh"),
            {"refresh": refresh_token},
            format="json",
        )

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)


class MentorChatAuthTests(APITestCase):
    def test_mentor_chat_requires_authentication(self):
        response = self.client.post(
            reverse("mentor-chat", kwargs={"mentor_slug": "any-mentor"}),
            {"message": "hello"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @mock.patch("mentors.api.views.chat_with_mentor")
    def test_mentor_chat_works_with_access_token(self, mock_chat_with_mentor):
        user_model = get_user_model()
        user_model.objects.create_user(
            username="matan",
            email="matan@example.com",
            password="StrongPass123",
        )

        login_response = self.client.post(
            reverse("auth-login"),
            {"username": "matan", "password": "StrongPass123"},
            format="json",
        )
        access_token = login_response.data["tokens"]["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        mock_chat_with_mentor.return_value = {
            "answer": "hello there",
            "sources": [],
        }

        response = self.client.post(
            reverse("mentor-chat", kwargs={"mentor_slug": "tech-mentor"}),
            {"message": "hello", "top_k": 3},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["answer"], "hello there")
        mock_chat_with_mentor.assert_called_once_with(
            mentor_slug="tech-mentor",
            message="hello",
            top_k=3,
        )
