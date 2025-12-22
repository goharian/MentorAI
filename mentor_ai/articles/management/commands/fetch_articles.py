from django.core.management.base import BaseCommand
from articles.services import fetch_and_store_articles
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fetches articles from the News API and stores them in the database.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting the article fetching task..."))
        
        try:
            articles_count = fetch_and_store_articles()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Success! {articles_count} new articles were saved.')
            )
            
        except Exception as e:
            logger.error(f"❌ Error while running the article fetching task: {e}")
            self.stdout.write(
                self.style.ERROR(f'❌ Error while running the article fetching task: {e}')
            )
