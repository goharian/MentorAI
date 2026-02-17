from django.apps import AppConfig


class MentorKnowledgeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mentor_knowledge"
    # Keep legacy app label for migration history and DB compatibility.
    label = "articles"
