import json
import os
import re

from sde_collections.models.candidate_url import CandidateURL
from sde_collections.models.collection import (
    Collection,
    CurationStatusChoices,
    WorkflowStatusChoices,
)
from sde_collections.models.collection_choice_fields import (
    ConnectorChoices,
    Divisions,
    DocumentTypes,
)
from sde_collections.models.pattern import ExcludePattern, TitlePattern
from sde_collections.tasks import (
    _get_data_to_import,
    pull_latest_collection_metadata_from_github,
)


def health_check(collection, server_name: str = "production") -> dict:
    """
    This method checks whether the rules defined in webapp are properly
    synced with Sinequa or not.

    Checks for Title Patterns, Exclude Patterns and Document Type Patterns.
    """
    health_check_report = []

    # get candidate URLs from sinequa
    candidate_urls_sinequa = _fetch_candidate_urls(collection, server_name)

    # check for title patterns
    title_pattern_report = _health_check_title_pattern(
        collection, candidate_urls_sinequa
    )
    health_check_report.extend(title_pattern_report)

    # check for exclude patterns
    exclude_pattern_report = _health_check_exclude_pattern(
        collection, candidate_urls_sinequa
    )
    health_check_report.extend(exclude_pattern_report)

    return health_check_report


def _fetch_candidate_urls(collection, server_name):
    # TODO: should we make it available throughout the project??
    candidate_urls_remote = _get_data_to_import(collection, server_name)

    candidate_urls_sinequa = {}
    for candidate_url in candidate_urls_remote:
        url = candidate_url["fields"]["url"]
        candidate_urls_sinequa[url] = CandidateURL(
            url=url, scraped_title=candidate_url["fields"]["scraped_title"]
        )
    return candidate_urls_sinequa


def _health_check_title_pattern(collection, candidate_urls_sinequa):
    collection_id = collection.pk
    collection_name = collection.name
    collection_config_folder = collection.config_folder
    curation_status = collection.curation_status
    workflow_status = collection.workflow_status

    title_pattern_report = []

    # now get Title Patterns in indexer db
    title_patterns_local = TitlePattern.objects.all().filter(
        collection_id=collection_id
    )

    # check if title patterns are porperly reflected in sinequa's response
    for title_pattern in title_patterns_local:
        pattern = title_pattern.title_pattern
        matched_urls = title_pattern.matched_urls()

        # now check to see if the matched_urls and candidate_urls_sinequa are similar or not
        for matched_url in matched_urls:
            url = matched_url.url
            if url in candidate_urls_sinequa:
                matched_title = matched_url.scraped_title
                sinequa_title = candidate_urls_sinequa[url].scraped_title

                if _resolve_title_pattern(pattern, sinequa_title) is None:
                    report = {
                        "id": collection_id,
                        "collection_name": collection_name,
                        "config_folder": collection_config_folder,
                        "curation_status": CurationStatusChoices.get_status_string(
                            curation_status
                        ),
                        "workflow_status": WorkflowStatusChoices.get_status_string(
                            workflow_status
                        ),
                        "pattern_name": "Title Pattern",
                        "pattern": pattern,
                        "scraped_title": matched_title,
                        "non_compliant_url": matched_url,
                    }
                    title_pattern_report.append(report)

    return title_pattern_report


def _health_check_exclude_pattern(collection, candidate_urls_sinequa):
    collection_id = collection.pk
    collection_name = collection.name
    collection_config_folder = collection.config_folder
    curation_status = collection.curation_status
    workflow_status = collection.workflow_status

    exclude_pattern_report = []

    # Perform exclude pattern check here
    exclude_patterns_local = ExcludePattern.objects.all().filter(
        collection_id=collection_id
    )

    def create_exclude_pattern_report(match_pattern, url):
        return {
            "id": collection_id,
            "collection_name": collection_name,
            "config_folder": collection_config_folder,
            "curation_status": CurationStatusChoices.get_status_string(curation_status),
            "workflow_status": WorkflowStatusChoices.get_status_string(workflow_status),
            "pattern_name": "Exclude Pattern",
            "pattern": match_pattern,
            "non_compliant_url": url,
        }

    for exclude_pattern in exclude_patterns_local:
        match_pattern = exclude_pattern.match_pattern

        # check with http://
        if match_pattern.find("http://") == -1:
            url = f"http://{match_pattern}"
            if url in candidate_urls_sinequa:
                exclude_pattern_report.append(
                    create_exclude_pattern_report(match_pattern, url)
                )

        if match_pattern.find("https://") == -1:
            url = f"https://{match_pattern}"
            if url in candidate_urls_sinequa:
                exclude_pattern_report.append(
                    create_exclude_pattern_report(match_pattern, url)
                )
        else:
            url = match_pattern  # assuming it has either https or http
            if url in candidate_urls_sinequa:
                exclude_pattern_report.append(
                    create_exclude_pattern_report(match_pattern, url)
                )

    return exclude_pattern_report


def _resolve_title_pattern(pattern, title):
    """
    Given a pattern check whether it is able to capture the title or not.

    E.g.: GCN {title}
    should capture :
        -> GCN - Notices
        -> GCN - News
    """
    pattern_with_whitespace = pattern.replace(" ", r"\s*-?\s*")

    parentheis_pattern = r"\{[^\}]+\}"
    multi_pattern = r"\/\/\*([^\/]*)\/a"

    def replace_parentheis_with_anything(match):
        return r"\S+"

    regex_pattern_parenthesis = re.sub(
        parentheis_pattern, replace_parentheis_with_anything, pattern_with_whitespace
    )
    regex_pattern = re.sub(
        multi_pattern, replace_parentheis_with_anything, regex_pattern_parenthesis
    )
    return re.match(regex_pattern, title)


def parse_int_values(github_value, db_value, field):
    """
    This method parses the integer values to their corresponding labels.
    """
    field_dict = {
        "division": Divisions,
        "document_type": DocumentTypes,
        "connector": ConnectorChoices,
    }
    try:
        github_value = field_dict[field](github_value).label
    except ValueError:
        github_value = None

    try:
        db_value = field_dict[field](db_value).label
    except ValueError:
        db_value = None

    return github_value, db_value


def generate_db_github_metadata_differences(reindex_configs_from_github=False):
    report = []

    fields = {
        "config_folder",
        "name",
        "url",
        "division",
        "document_type",
        "connector",
    }

    # for each folder in github get the metadata from the default.xml file
    FILENAME = "github_collections.json"
    if os.path.exists(FILENAME) and not reindex_configs_from_github:
        collections = json.load(open(FILENAME))
    else:
        pull_latest_collection_metadata_from_github.delay()

    # also fetch same metadata from the database
    for collection in collections:
        # fix division to be the same as in the database
        collection["division"] = Divisions.lookup_by_text(collection["division"])
        config_folder = collection["config_folder"]
        try:
            db_collection = Collection.objects.get(config_folder=config_folder)
        except Collection.DoesNotExist:
            report.append(
                {
                    "config_folder": config_folder,
                    "field": "config_folder",
                    "github_value": config_folder,
                    "db_value": "DoesNotExist",
                }
            )
            continue

        # check if there is any difference in the metadata
        # if there is a difference then add it to the report
        int_fields = {"division", "document_type", "connector"}
        for field in fields:
            if collection[field] != getattr(db_collection, field):
                db_value = getattr(db_collection, field)
                if field in int_fields:
                    collection[field], db_value = parse_int_values(
                        collection[field], db_value, field
                    )

                report.append(
                    {
                        "config_folder": config_folder,
                        "field": field,
                        "github_value": collection[field],
                        "db_value": db_value,
                    }
                )

    # check if there are any collections in the database that are not in github
    for db_collection in Collection.objects.exclude(
        config_folder__in=[c["config_folder"] for c in collections]
    ):
        report.append(
            {
                "config_folder": db_collection.config_folder,
                "field": "config_folder",
                "github_value": "DoesNotExist",
                "db_value": db_collection.config_folder,
            }
        )

    return report
