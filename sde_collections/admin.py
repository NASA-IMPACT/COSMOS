from django.contrib import admin

from .models import Collection, Division


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    """Admin View for Collection"""

    list_display = ("name", "config_folder", "url", "division", "turned_on")


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    """Admin View for Division"""

    list_display = (
        "id",
        "name",
    )
