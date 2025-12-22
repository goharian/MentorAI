from rest_framework import serializers
from .models import Article

class ArticleListSerializer(serializers.ModelSerializer):
    """
    Serializer to display a list of articles (basic data).
    """
    class Meta:
        model = Article
        fields = ('id', 'title', 'url', 'published_date', 'source')


class ArticleDetailSerializer(serializers.ModelSerializer):
    """
    Serializer to display single article details (including full content).
    # """
    class Meta:
        model = Article
        fields = ('id', 'title', 'content', 'url', 'published_date', 'source')


class ArticleSummarySerializer(serializers.Serializer):
    """
    Serializer to display article summary.
    """
    summary = serializers.CharField()
    cached = serializers.BooleanField()