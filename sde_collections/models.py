from django.db import models


class Collection(models.Model):
    """Model definition for Collection."""

    name = models.CharField("Name", max_length=1024)

    class Meta:
        """Meta definition for Collection."""

        verbose_name = "Collection"
        verbose_name_plural = "Collections"

    def __str__(self):
        """Unicode representation of Collection."""
        return self.name
