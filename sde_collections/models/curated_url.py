from .url import Url


class CuratedUrl(Url):
    """Model for storing curated and live URLs after the curation process."""

    class Meta:
        verbose_name = "Curated URL"
        verbose_name_plural = "Curated URLs"
