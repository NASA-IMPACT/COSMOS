from django.db import models


class Division(models.Model):
    """Model definition for Division."""

    name = models.CharField("Name", max_length=512)

    class Meta:
        """Meta definition for Division."""

        verbose_name = "Division"
        verbose_name_plural = "Divisions"

    def __str__(self):
        """Unicode representation of Division."""
        return self.name


class Collection(models.Model):
    """Model definition for Collection."""

    name = models.CharField("Name", max_length=1024)
    config_folder = models.CharField("Config Folder", max_length=2048)
    url = models.URLField("URL", max_length=2048)
    division = models.ForeignKey(Division, on_delete=models.CASCADE)
    turned_on = models.BooleanField("Turned On", default=True)

    class Meta:
        """Meta definition for Collection."""

        verbose_name = "Collection"
        verbose_name_plural = "Collections"

    def __str__(self):
        """Unicode representation of Collection."""
        return self.name

    @property
    def indexed(self):
        return self.config_folder != ""
