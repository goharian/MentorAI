from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, ArticleSummaryView

router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')

urlpatterns = [
    path('', include(router.urls)),
    
    path('articles/<int:pk>/summary', ArticleSummaryView.as_view(), name='article-summary'),
]