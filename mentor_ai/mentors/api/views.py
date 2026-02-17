from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema

from mentors.api.serializers import (
    AuthResponseSerializer,
    LoginSerializer,
    MentorChatResponseSerializer,
    MentorChatSerializer,
    RegisterSerializer,
)
from mentors.services.chat_service import chat_with_mentor


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Register a new user",
        request=RegisterSerializer,
        responses={201: AuthResponseSerializer},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

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

    @extend_schema(
        tags=["Auth"],
        summary="Login and receive JWT tokens",
        request=LoginSerializer,
        responses={200: AuthResponseSerializer},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

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

    @extend_schema(
        tags=["Mentors"],
        summary="Chat with a mentor persona",
        parameters=[
            OpenApiParameter(
                name="mentor_slug",
                location=OpenApiParameter.PATH,
                required=True,
                type=OpenApiTypes.STR,
                description="Mentor slug (for example: 'elon-musk').",
            )
        ],
        request=MentorChatSerializer,
        responses={200: MentorChatResponseSerializer},
    )
    def post(self, request, mentor_slug: str):
        serializer = MentorChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payload = chat_with_mentor(
            mentor_slug=mentor_slug,
            message=serializer.validated_data["message"],
            top_k=serializer.validated_data["top_k"],
        )

        return Response(
            {"mentor_slug": mentor_slug, **payload},
            status=status.HTTP_200_OK,
        )
