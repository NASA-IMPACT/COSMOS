import time

from django.core.management.base import BaseCommand
from django.db.models import Count, Min

from sde_collections.models.candidate_url import CandidateURL
from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import WorkflowStatusChoices


class Command(BaseCommand):
    help = "Deduplicate CandidateURLs"

    def handle(self, *args, **kwargs):
        deduplicate_candidate_urls()


def is_priority_collection(collection):
    priority_statuses = {
        WorkflowStatusChoices.CURATED,
        WorkflowStatusChoices.QUALITY_FIXED,
        WorkflowStatusChoices.SECRET_DEPLOYMENT_STARTED,
        WorkflowStatusChoices.SECRET_DEPLOYMENT_FAILED,
        WorkflowStatusChoices.READY_FOR_LRM_QUALITY_CHECK,
        WorkflowStatusChoices.READY_FOR_FINAL_QUALITY_CHECK,
        WorkflowStatusChoices.QUALITY_CHECK_FAILED,
        WorkflowStatusChoices.QUALITY_CHECK_MINOR,
        WorkflowStatusChoices.QUALITY_CHECK_PERFECT,
        WorkflowStatusChoices.PROD_PERFECT,
        WorkflowStatusChoices.PROD_MINOR,
        WorkflowStatusChoices.PROD_MAJOR,
    }
    return collection.workflow_status in priority_statuses


def deduplicate_candidate_urls():
    start_time = time.time()

    collection_counts = {
        c["id"]: c["url_count"]
        for c in Collection.objects.annotate(url_count=Count("candidate_urls")).values("id", "url_count")
    }

    collection_status = {c.id: is_priority_collection(c) for c in Collection.objects.all()}

    # Phase 1: Intra-collection duplicates
    intra_dupes = (
        CandidateURL.objects.values("collection_id", "url")
        .annotate(count=Count("id"), min_id=Min("id"))
        .filter(count__gt=1)
    )

    intra_ids_to_delete = []
    for dupe in intra_dupes:
        dupe_ids = set(
            CandidateURL.objects.filter(collection_id=dupe["collection_id"], url=dupe["url"])
            .exclude(id=dupe["min_id"])
            .values_list("id", flat=True)
        )
        intra_ids_to_delete.extend(dupe_ids)

    CandidateURL.objects.filter(id__in=intra_ids_to_delete).delete()

    # Phase 2: Cross-collection duplicates
    cross_dupes = CandidateURL.objects.values("url").annotate(count=Count("id")).filter(count__gt=1)

    cross_ids_to_delete = []
    for dupe in cross_dupes:
        instances = list(CandidateURL.objects.filter(url=dupe["url"]).values("id", "collection_id"))

        priority_instances = [i for i in instances if collection_status[i["collection_id"]]]
        non_priority_instances = [i for i in instances if not collection_status[i["collection_id"]]]

        if priority_instances:
            keep_instance = min(priority_instances, key=lambda x: collection_counts[x["collection_id"]])
        else:
            keep_instance = min(non_priority_instances, key=lambda x: collection_counts[x["collection_id"]])

        delete_ids = [i["id"] for i in instances if i["id"] != keep_instance["id"]]
        cross_ids_to_delete.extend(delete_ids)

    CandidateURL.objects.filter(id__in=cross_ids_to_delete).delete()

    elapsed_time = time.time() - start_time
    action = "Deleted"
    print(
        f"{action} {len(intra_ids_to_delete)} intra-collection and {len(cross_ids_to_delete)} cross-collection duplicates (total: {len(intra_ids_to_delete) + len(cross_ids_to_delete)}) in {elapsed_time:.2f} seconds"  # noqa
    )
