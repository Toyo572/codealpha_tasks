from django.conf import settings
from django.db import models


class ShortenedURL(models.Model):
    short_code = models.CharField(max_length=10, unique=True, db_index=True)
    original_url = models.URLField(max_length=2048)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shortened_urls",
    )
    hits = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "shortened_urls"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.short_code} → {self.original_url}"