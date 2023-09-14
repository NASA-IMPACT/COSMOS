from typing import Dict

from sde_collections.models.pattern import (
    TitlePattern,
    ExcludePattern,
    DocumentTypePattern)
from sde_collections.models.collection import Collection
from sde_collections.tasks import _get_data_to_import


def check_rules_sync(server_name: str = "production") -> Dict:
    """
        This method checks whether the rules defined in webapp are properly
        synced with Sinequa or not. 

        Checks for Title Patterns, Exclude Patterns and Document Type Patterns.
    """
    collections = Collection.objects.all().filter(delete=False)

    sync_check_report = []

    for collection in collections:
        collection_id = collection.pk
        collection_name = collection.name
        collection_config_folder = collection.config_folder
        curation_status = collection.curation_status

        print("collection_name -->", collection_name)

        # TODO: should we make it available throughout the project??
        candidate_urls_sinequa = _get_data_to_import(collection, server_name)
        print("Total candidate URLs-->", len(candidate_urls_sinequa))

        # now get Title Patterns in indexer db
        title_patterns_local = TitlePattern.objects.all().filter(collection_id=collection_id)

        # check if title patterns are porperly reflected in sinequa's response
        for title_pattern in title_patterns_local:
            pattern = title_pattern.title_pattern

            title_pattern.match_pattern = pattern

            # TODO: get list of candidate URLs for given pattern and
            # TODO: check which URLs match with the given pattern and which do not.

            # for all the candidate urls
            for candidate_url in candidate_urls_sinequa:
                url = candidate_url["fields"]["url"]
                scraped_title = candidate_url["fields"]["scraped_title"]

                if scraped_title != pattern:
                    report = {
                        "id": collection_id,
                        "collection_name": collection_name,
                        "config_folder": collection_config_folder,
                        "curation_status": curation_status,  # TODO: change this to actual value
                        "pattern_name": "Title Pattern",
                        "pattern": pattern,
                        "scraped_title": scraped_title,
                        "non_compliant_url": url,
                    }
                    sync_check_report.append(report)

        # Perform exclude pattern check here
        exclude_patterns_local = ExcludePattern.objects.all().filter(collection_id=collection_id)

        for exclude_pattern in exclude_patterns_local:
            match_pattern = exclude_pattern.match_pattern

            for candidate_url in candidate_urls_sinequa:
                # TODO: check exclude pattern here
                break
            break

        # perform document type pattern check here
        document_type_patterns_local = DocumentTypePattern.objects.all().filter(collection_id=collection_id)

        for document_type_pattern in document_type_patterns_local:
            print("document type pattern:")
            print(document_type_pattern)

            for candidate_url in candidate_urls_sinequa:
                # TODO: check document type pattern here
                break
            break

        break

    return sync_check_report
