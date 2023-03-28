from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import CandidateURL, Collection, Division


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


class CandidateURLAdmin(TreeAdmin):
    """Admin View for CandidateURL"""

    form = movenodeform_factory(CandidateURL)
    list_display = ("url", "title", "excluded")


admin.site.register(CandidateURL, CandidateURLAdmin)
