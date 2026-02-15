from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("articles", "0004_contentchunk_mentor_videocontent_delete_article_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="videocontent",
            name="status",
            field=models.CharField(
                choices=[
                    ("new", "New"),
                    ("queued", "Queued"),
                    ("fetched", "Transcript fetched"),
                    ("chunked", "Chunked"),
                    ("embedded", "Embedded"),
                    ("ready", "Ready"),
                    ("failed", "Failed"),
                ],
                default="new",
                max_length=20,
            ),
        ),
    ]
