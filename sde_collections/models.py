from django.db import models
from treebeard.mp_tree import MP_Node


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

    def candidate_url_tree(self):
        tree = {}
        top_level_items = self.candidateurl_set.filter(parent__isnull=True)
        for item in top_level_items:
            tree[item.url] = item.get_tree()
        return tree


class CandidateURL(MP_Node):
    """A candidate URL scraped for a given collection."""

    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    url = models.CharField("URL", max_length=2048)
    excluded = models.BooleanField(default=False)
    title = models.CharField("Title", max_length=2048)

    node_order_by = ["url"]

    class Meta:
        """Meta definition for Candidate URL."""

        verbose_name = "Candidate URL"
        verbose_name_plural = "Candidate URLs"

    def __str__(self):
        return self.url
