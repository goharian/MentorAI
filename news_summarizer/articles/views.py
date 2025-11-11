from rest_framework import viewsets, generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Article
from .serializers import ArticleListSerializer, ArticleDetailSerializer, ArticleSummarySerializer
from .chatgpt_service import get_article_summary_with_caching


class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    - GET /articles: paginated list.
    - GET /articles/{id}: article details.
    """
    queryset = Article.objects.all()

    def get_serializer_class(self):
        """
        return List Serializer for a list and Detail Serializer for a single article
        """
        if self.action == 'list':
            return ArticleListSerializer
        return ArticleDetailSerializer


class ArticleSummaryView(APIView):
    """
    Returns the article summary, using Caching and the ChatGPT service.
    Endpoint: GET /articles/{id}/summary
    """
    def get(self, request, pk):
        article = get_object_or_404(Article, pk=pk)
        summary_text, cached = get_article_summary_with_caching(article.title, article.content)

        serializer = ArticleSummarySerializer({
            'summary': summary_text,
            'cached': cached
        })

        return Response(serializer.data, status=status.HTTP_200_OK)