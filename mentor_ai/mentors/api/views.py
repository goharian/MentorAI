from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from mentors.api.serializers import MentorChatSerializer
from mentors.services.chat_service import chat_with_mentor


class MentorChatView(APIView):
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
