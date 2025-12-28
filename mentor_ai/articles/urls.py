from rest_framework.routers import DefaultRouter
from .views import MentorViewSet, VideoContentViewSet, ContentChunkViewSet

router = DefaultRouter()
router.register(r"mentors", MentorViewSet)
router.register(r"videos", VideoContentViewSet)
router.register(r"chunks", ContentChunkViewSet)

urlpatterns = router.urls
