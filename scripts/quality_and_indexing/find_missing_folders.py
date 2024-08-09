import os
from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import WorkflowStatusChoices
from sde_collections.utils.github_helper import GitHubHandler


def get_sources_by_status(statuses):
    """Fetch sources by workflow status."""
    return Collection.objects.filter(workflow_status__in=statuses)


def get_missing_folders(collections, base_directory, github_handler):
    """Find collections missing specific folders in the base directory."""
    missing = []
    for source in collections:
        folder_path = os.path.join(base_directory, source.config_folder, "default.xml")
        if not github_handler.check_file_exists(folder_path):
            missing.append(source)
    return missing


def get_difference(queryset, *exclude_lists):
    """Return queryset minus elements in exclude_lists based on config_folder."""
    exclude_folders = {item.config_folder for sublist in exclude_lists for item in sublist}
    return [item for item in queryset if item.config_folder not in exclude_folders]


def print_configs(queryset):
    """Print the config folder paths of the collections in the queryset."""
    for source in queryset:
        print(source.config_folder)
    print("---" * 20)
    print()


# initial sources list
print("sources_to_fix")
print_configs(get_sources_by_status([WorkflowStatusChoices.QUALITY_FIXED]))

print("sources_to_curated")
print_configs(get_sources_by_status([WorkflowStatusChoices.CURATED]))

all_relevant_sources = get_sources_by_status([WorkflowStatusChoices.QUALITY_FIXED, WorkflowStatusChoices.CURATED])

# broken sources list
github_handler = GitHubHandler()
print("missing_scraper_folders")
missing_scraper_folders = get_missing_folders(all_relevant_sources, "sources/scrapers/", github_handler)
print_configs(missing_scraper_folders)

print("missing_plugin_folders")
missing_plugin_folders = get_missing_folders(all_relevant_sources, "sources/SDE/", github_handler)
print_configs(missing_plugin_folders)


# final sources list
final_sources = get_difference(all_relevant_sources, missing_scraper_folders, missing_plugin_folders)
print("final_sources")
print_configs(final_sources)
