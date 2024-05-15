"""
adds collections marked as ready for public prod to the public query
after running this code, you will need to merge in the webapp branch
"""

from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import WorkflowStatusChoices

for collection in Collection.objects.filter(workflow_status=WorkflowStatusChoices.READY_FOR_PUBLIC_PROD):
    print(collection.config_folder)
    collection.add_to_public_query()
