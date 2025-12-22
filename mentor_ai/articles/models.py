"""
Article model for storing news articles.
"""
from django.db import models
from django.core.validators import MinLengthValidator


class Article(models.Model):
    """Article object."""
    id = models.AutoField(primary_key=True)
    title = models.CharField(
        max_length=512,
        validators=[MinLengthValidator(5, "Title must be at least 5 characters long.")]
    )
    content = models.TextField(
        null=True, 
        blank=True,
        validators=[MinLengthValidator(20, "Content must be at least 20 characters long.")]
    )
    url = models.URLField(unique=True,max_length=2000)
    published_date = models.DateTimeField()
    source = models.CharField(max_length=255)


    class Meta:
        """
        Meta data for Article model.
        """
        ordering = ["-published_date"]

    def __str__(self):
        """
        String representation of the Article object.
        """
        return self.title