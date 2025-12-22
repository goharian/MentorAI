from django.test import TestCase
from articles.models import Article

class ArticleModelTest(TestCase):
    """
    Tests for the Article model.
    """

    def test_article_creation(self):
        """
        Test that an Article instance can be created successfully.
        """
        article = Article.objects.create(
            title="Test Article",
            content="This is a test article content.",
            url="https://example.com/test-article",
            published_date="2023-01-01T12:00:00Z",
            source="Example Source"
        )
        self.assertIsInstance(article, Article)
        self.assertEqual(Article.objects.count(), 1)
        self.assertEqual(article.title, "Test Article")

    def test_article_str_representation(self):
        """
        Test the string representation of the Article model.
        """
        article = Article.objects.create(
            title="Another Test Article",
            content="Content for another test article.",
            url="https://example.com/another-test-article",
            published_date="2023-01-02T12:00:00Z",
            source="Another Source"
        )
        self.assertEqual(str(article), "Another Test Article")