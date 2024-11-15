import factory
from django.contrib.auth import get_user_model
from django.utils import timezone

from sde_collections.models.candidate_url import CandidateURL
from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import (
    ConnectorChoices,
    Divisions,
    DocumentTypes,
    UpdateFrequencies,
    WorkflowStatusChoices,
)

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")


class CollectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Collection

    name = factory.Faker("company")
    config_folder = factory.Sequence(
        lambda n: f"config_folder_{n}"
    )  # might need to update this to be calculated based on name?
    url = factory.Faker("url")
    division = Divisions.ASTROPHYSICS
    connector = ConnectorChoices.CRAWLER2
    update_frequency = UpdateFrequencies.WEEKLY
    document_type = DocumentTypes.DOCUMENTATION
    delete = False
    is_multi_division = False

    github_issue_number = factory.Sequence(lambda n: n)
    notes = factory.Faker("paragraph")
    updated_at = factory.LazyFunction(timezone.now)
    new_collection = False

    workflow_status = WorkflowStatusChoices.RESEARCH_IN_PROGRESS
    tracker = factory.Maybe("workflow_status")

    # ForeignKey to User for `curated_by`
    curated_by = factory.SubFactory(UserFactory)
    curation_started = factory.LazyFunction(timezone.now)


class CandidateURLFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CandidateURL

    collection = factory.SubFactory(CollectionFactory)
    url = factory.Faker("url")
    hash = factory.LazyFunction(lambda: "1")
    scraped_title = factory.Faker("sentence")
    generated_title = factory.Faker("sentence")
    test_title = ""
    production_title = ""
    level = 0
    visited = False
    document_type = DocumentTypes.DOCUMENTATION
    division = Divisions.ASTROPHYSICS
    inferenced_by = ""
    is_pdf = False
    present_on_test = False
    present_on_prod = False
    is_tdamm = False
