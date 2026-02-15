from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from mentors.api.serializers import LoginSerializer, MentorChatSerializer, RegisterSerializer
from mentors.services.chat_service import chat_with_mentor


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_200_OK,
        )


class MentorChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, mentor_slug: str):
        ser = MentorChatSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        payload = chat_with_mentor(
            mentor_slug=mentor_slug,
            message=ser.validated_data["message"],
            top_k=ser.validated_data["top_k"],
        )

        return Response(
            {"mentor_slug": mentor_slug, **payload},
            status=status.HTTP_200_OK,
        )
