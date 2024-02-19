from django.contrib import admin  # noqa

from .models import EnvironmentalJusticeRow


@admin.register(EnvironmentalJusticeRow)
class EnvironmentalJusticeAdmin(admin.ModelAdmin):
    """Admin View for EnvironmentalJustice"""

    list_display = ("dataset", "description")
