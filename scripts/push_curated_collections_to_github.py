from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import WorkflowStatusChoices
from sde_collections.utils.github_helper import GitHubHandler


def push_curated_collections_to_github():
    # Filter collections with a specific workflow status (CURATED)
    collections = Collection.objects.filter(workflow_status=WorkflowStatusChoices.CURATED)

    # Initialize the GitHub handler and push collections
    github_handler = GitHubHandler(collections)
    github_handler.push_to_github()
    print("Curated collections with a workflow status of CURATED have been pushed to GitHub.")


if __name__ == "__main__":
    push_curated_collections_to_github()
