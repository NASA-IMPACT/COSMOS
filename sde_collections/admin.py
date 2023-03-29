from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import CandidateURL, Collection


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    """Admin View for Collection"""

    list_display = ("name", "config_folder", "url", "division", "turned_on")


@admin.action(description="Exclude URL and all children")
def exclude_pattern(modeladmin, request, queryset):
    queryset.update(excluded=True)


class CandidateURLAdmin(TreeAdmin):
    """Admin View for CandidateURL"""

    form = movenodeform_factory(CandidateURL)
    list_display = ("url", "title", "excluded")
    actions = [exclude_pattern]


admin.site.register(CandidateURL, CandidateURLAdmin)
