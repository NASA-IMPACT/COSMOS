import time

from django.db.models import Count, Min

from sde_collections.models.candidate_url import CandidateURL
from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import WorkflowStatusChoices


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

    # Keep the existing collection preprocessing
    collection_counts = {
        c["id"]: c["url_count"]
        for c in Collection.objects.annotate(url_count=Count("candidate_urls")).values("id", "url_count")
    }
    collection_status = {c.id: is_priority_collection(c) for c in Collection.objects.all()}

    # Phase 1: Intra-collection duplicates (keep this part the same)
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

    # Phase 2: Modified Cross-collection duplicates
    cross_dupes = CandidateURL.objects.values("url").annotate(count=Count("id")).filter(count__gt=1)

    cross_ids_to_delete = []
    for dupe in cross_dupes:
        # Get all instances of this URL with their relevant data
        instances = list(CandidateURL.objects.filter(url=dupe["url"]).order_by("id").values("id", "collection_id"))

        while len(instances) > 1:  # Process until we only have one instance left
            # Create comparison data for each instance
            instance_data = [
                {
                    "id": inst["id"],
                    "collection_id": inst["collection_id"],
                    "is_priority": collection_status[inst["collection_id"]],
                    "url_count": collection_counts[inst["collection_id"]],
                }
                for inst in instances
            ]

            # Find the instance to keep based on the new rules
            def get_instance_to_delete(instances_list):
                # First, separate by priority
                priority_instances = [i for i in instances_list if i["is_priority"]]
                non_priority_instances = [i for i in instances_list if not i["is_priority"]]

                # If we have both priority and non-priority, delete from non-priority
                if priority_instances and non_priority_instances:
                    return non_priority_instances[0]

                # If all instances are of same priority type, compare url counts
                working_list = priority_instances if priority_instances else non_priority_instances
                min_count = min(i["url_count"] for i in working_list)
                lowest_count_instances = [i for i in working_list if i["url_count"] == min_count]

                # If multiple instances have the same count, take the one with lowest ID
                return min(lowest_count_instances, key=lambda x: x["id"])

            # Get the instance to delete
            instance_to_delete = get_instance_to_delete(instance_data)

            # Add it to our delete list and remove from instances
            cross_ids_to_delete.append(instance_to_delete["id"])
            instances = [inst for inst in instances if inst["id"] != instance_to_delete["id"]]

    CandidateURL.objects.filter(id__in=cross_ids_to_delete).delete()

    elapsed_time = time.time() - start_time
    action = "Deleted"
    print(
        f"{action} {len(intra_ids_to_delete)} intra-collection and {len(cross_ids_to_delete)} "
        f"cross-collection duplicates (total: {len(intra_ids_to_delete) + len(cross_ids_to_delete)}) "
        f"in {elapsed_time:.2f} seconds"
    )
