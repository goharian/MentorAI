from unittest import mock
from django.urls import reverse
from django.test import TestCase, Client
from articles.models import Article

class ArticleViewsTest(TestCase):
    """
    Tests for article-related views.
    """
    def test_article_summary_view_returns_summary_and_cached_flag(self):
        """
        Test that the article summary view returns the summary and cached flag.
        """
        from django.utils import timezone

        # Create an article in the test database
        article = Article.objects.create(
            title="View Test",
            content="Some content for the view test",
            url="https://example.com/article",
            published_date=timezone.now(),
            source="Example"
        )

        # Patch the function imported in the views module
        with mock.patch(
            "articles.views.get_article_summary_with_caching",
            return_value=("View summary", True)
        ):
            client = self.client
            resp = client.get(f"/articles/{article.pk}/summary")

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("summary"), "View summary")
        self.assertTrue(data.get("cached"))