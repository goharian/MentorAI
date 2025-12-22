from django.test import TestCase, override_settings
from unittest import mock
from django.utils import timezone
from ..models import Article
from ..services import fetch_and_store_articles
import requests

class ServicesTests(TestCase):
	"""
	Tests for article services.
	"""

	@mock.patch('articles.services.process_and_save_article_task')
	@mock.patch('articles.services.requests.get')
	def test_fetch_and_store_articles_sends_to_celery_task(self, mock_requests_get, mock_celery_task):
		"""
		Test that fetch_and_store_articles fetches articles and sends them to Celery task.
		"""

		fake_article = {
			'url': 'https://example.com/new-1',
			'title': 'New Article',
			'content': 'Content here',
			'publishedAt': '2020-01-01T12:00:00Z',
			'source': {'name': 'Example'}
		}

		fake_response = mock.Mock()
		fake_response.raise_for_status = mock.Mock()
		fake_response.json.return_value = {'articles': [fake_article, fake_article]}
		mock_requests_get.return_value = fake_response

		with override_settings(NEWS_API_URL='https://api.test', NEWS_API_KEY='key', NEWS_API_QUERY='q'):
			saved = fetch_and_store_articles()

		self.assertEqual(saved, 2)
		mock_celery_task.delay.assert_called()
		self.assertEqual(mock_celery_task.delay.call_count, 2)

	def test_fetch_and_store_articles_handles_request_exception(self):
		"""
		Test that fetch_and_store_articles handles RequestException gracefully.
		"""

		with override_settings(NEWS_API_URL='https://api.test', NEWS_API_KEY='key', NEWS_API_QUERY='q'):
			with mock.patch('articles.services.requests.get', side_effect=requests.exceptions.RequestException("fail")):
				result = fetch_and_store_articles()

		self.assertEqual(result, 0)