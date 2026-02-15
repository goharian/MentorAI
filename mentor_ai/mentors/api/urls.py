from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from mentors.api.views import LoginView, MentorChatView, RegisterView

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("mentors/<slug:mentor_slug>/chat/", MentorChatView.as_view(), name="mentor-chat"),
]
