"""
Database models.
"""
from django.db import models


class Article(models.Model):
    """Article object."""
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=512)
    content = models.TextField(null=True, blank=True)
    url = models.URLField(unique=True,max_length=2000)
    published_date = models.DateTimeField()
    source = models.CharField(max_length=255)


    class Meta:
        ordering = ["-published_date"]

    def __str__(self):
        return self.title