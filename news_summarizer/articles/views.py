from rest_framework import viewsets, generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Article
from .serializers import ArticleListSerializer, ArticleDetailSerializer, ArticleSummarySerializer
from .chatgpt_service import get_article_summary_with_caching
from .pagination import StandardResultsSetPagination

class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving articles.
    Endpoints:
    - GET /articles: paginated list.
    - GET /articles/{id}: article details.
    """
    queryset = Article.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        """
        Determine the serializer class based on the action.
        Returns:
            Serializer class based on action.
        """
        if self.action == 'list':
            return ArticleListSerializer
        return ArticleDetailSerializer


class ArticleSummaryView(APIView):
    """
    View for retrieving article summaries.
    Returns the article summary, using Caching and the ChatGPT service.
    Endpoint: GET /articles/{id}/summary
    """
    def get(self, request, pk):
        """
        Get the summary for a specific article by its ID.
        Args:
            request: The HTTP request object.
            pk: Primary key of the article.
        Returns:
            Response: JSON response containing the article summary.
        """ 
        article = get_object_or_404(Article, pk=pk)
        summary_text, cached = get_article_summary_with_caching(article.title, article.content)

        serializer = ArticleSummarySerializer({
            'summary': summary_text,
            'cached': cached
        })

        return Response(serializer.data, status=status.HTTP_200_OK)