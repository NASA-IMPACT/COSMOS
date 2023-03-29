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
    for candidate_url in queryset.all():
        candidate_url.set_excluded(True)


@admin.action(description="Include URL and all children")
def include_pattern(modeladmin, request, queryset):
    for candidate_url in queryset.all():
        candidate_url.set_excluded(False)


@admin.action(description="Exclude pattern and delete children")
def exclude_and_delete_children(modeladmin, request, queryset):
    queryset.update(excluded=True)
    for candidate_url in queryset.all():
        candidate_url.get_children().delete()


class CandidateURLAdmin(TreeAdmin):
    """Admin View for CandidateURL"""

    form = movenodeform_factory(CandidateURL)
    list_display = ("url", "title", "excluded")
    list_filter = ("collection", "excluded")
    actions = [exclude_pattern, include_pattern, exclude_and_delete_children]


admin.site.register(CandidateURL, CandidateURLAdmin)
