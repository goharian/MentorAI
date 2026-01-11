from django.urls import path
from mentors.api.views import MentorChatView

urlpatterns = [
    path("mentors/<slug:mentor_slug>/chat/", MentorChatView.as_view(), name="mentor-chat"),
]
