from typing import Dict

from sde_collections.models.pattern import (
    TitlePattern,
    ExcludePattern,
    DocumentTypePattern)
from sde_collections.models.candidate_url import CandidateURL
from sde_collections.tasks import _get_data_to_import

import re


def health_check(collection, server_name: str = "production") -> Dict:
    """
        This method checks whether the rules defined in webapp are properly
        synced with Sinequa or not. 

        Checks for Title Patterns, Exclude Patterns and Document Type Patterns.
    """
    health_check_report = []

    collection_id = collection.pk
    collection_name = collection.name
    collection_config_folder = collection.config_folder
    curation_status = collection.curation_status

    candidate_urls_sinequa = _fetch_candidate_urls(collection, server_name)
    print(candidate_urls_sinequa)

    # now get Title Patterns in indexer db
    title_patterns_local = TitlePattern.objects.all().filter(collection_id=collection_id)

    # check if title patterns are porperly reflected in sinequa's response
    for title_pattern in title_patterns_local:
        pattern = title_pattern.title_pattern
        matched_urls = title_pattern.matched_urls()

        # now check to see if the matched_urls and canidate_urls_sinequa are similar or not
        for matched_url in matched_urls:
            url = matched_url.url
            if url in candidate_urls_sinequa:
                matched_title = matched_url.scraped_title
                sinequa_title = candidate_urls_sinequa[url].scraped_title

                if _title_pattern_resolver(pattern, sinequa_title) is None:
                    report = {
                        "id": collection_id,
                        "collection_name": collection_name,
                        "config_folder": collection_config_folder,
                        "curation_status": curation_status,  # TODO: change this to actual value
                        "pattern_name": "Title Pattern",
                        "pattern": pattern,
                        "scraped_title": matched_title,
                        "non_compliant_url": matched_url,
                    }
                    health_check_report.append(report)

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

    return health_check_report


def _fetch_candidate_urls(collection, server_name):
    # TODO: should we make it available throughout the project??
    candidate_urls_remote = _get_data_to_import(collection, server_name)
    print("Total candidate URLs-->", len(candidate_urls_remote))

    candidate_urls_sinequa = {}
    for candidate_url in candidate_urls_remote:
        url = candidate_url["fields"]["url"]
        scraped_title = candidate_url["fields"]["scraped_title"]
        candidate_urls_sinequa[url] = CandidateURL(
            url=url,
            scraped_title=scraped_title
        )
    return candidate_urls_sinequa


def _title_pattern_resolver(pattern, title):
    """
        Given a pattern check whether it is able to capture the title or not. 

        E.g.: GCN {title} 
        should capture : 
            -> GCN - Notices
            -> GCN - News
    """
    pattern_with_whitespace = pattern.replace(" ", "\s*-?\s*")

    parentheis_pattern = r'\{[^\}]+\}'
    multi_pattern = r'\/\/\*([^\/]*)\/a'

    def replace_parentheis_with_anything(match):
        return r'\S+'

    regex_pattern_parenthesis = re.sub(parentheis_pattern, replace_parentheis_with_anything, pattern_with_whitespace)
    regex_pattern = re.sub(multi_pattern, replace_parentheis_with_anything, regex_pattern_parenthesis)
    print("regex pattern: ", regex_pattern)
    return re.match(regex_pattern, title)
