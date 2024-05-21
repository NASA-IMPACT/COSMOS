"""you run this in the shell on the server to find sources to index and find any that are missing plugin folders"""

import os

from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import WorkflowStatusChoices
from sde_collections.utils.github_helper import GitHubHandler


def get_sources_to_fix():
    return Collection.objects.filter(workflow_status__in=[WorkflowStatusChoices.QUALITY_FIXED])


def get_sources_to_index():
    return Collection.objects.filter(workflow_status__in=[WorkflowStatusChoices.CURATED])


def get_all_relevant_sources():
    return Collection.objects.filter(
        workflow_status__in=[WorkflowStatusChoices.QUALITY_FIXED, WorkflowStatusChoices.CURATED]
    )


def get_missing_folders(collections, base_directory):
    gh = GitHubHandler()
    missing = []
    for source in collections:
        folder_path = os.path.join(base_directory, source.config_folder, "default.xml")
        if not gh.check_file_exists(folder_path):
            missing.append(source)
    return missing


def print_configs(queryset):
    for source in queryset:
        print(source.config_folder)
    print("---" * 20)
    print()


print("sources_to_fix")
sources_to_fix = get_sources_to_fix()
print_configs(sources_to_fix)


print("sources_to_index")
sources_to_index = get_sources_to_index()
print_configs(sources_to_index)


all_relevant_sources = get_all_relevant_sources()

print("missing_scraper_folders")
missing_folders = get_missing_folders(all_relevant_sources, "sources/scrapers/")
print_configs(missing_folders)


print("missing_plugin_folders")
missing_folders = get_missing_folders(all_relevant_sources, "sources/SDE/")
print_configs(missing_folders)
