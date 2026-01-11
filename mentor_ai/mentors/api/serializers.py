from rest_framework import serializers


class MentorChatSerializer(serializers.Serializer):
    message = serializers.CharField(min_length=1, max_length=8000)
    top_k = serializers.IntegerField(required=False, min_value=1, max_value=12, default=6)