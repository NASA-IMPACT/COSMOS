import factory
from django.contrib.auth import get_user_model
from django.utils import timezone

from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import (
    ConnectorChoices,
    Divisions,
    DocumentTypes,
    UpdateFrequencies,
    WorkflowStatusChoices,
)
from sde_collections.models.delta_url import CuratedUrl, DeltaUrl, DumpUrl

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


class DumpUrlFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DumpUrl

    collection = factory.SubFactory(CollectionFactory)
    url = factory.Faker("url")
    scraped_title = factory.Faker("sentence")
    scraped_text = factory.Faker("paragraph")
    # generated_title = factory.Faker("sentence")
    # visited = factory.Faker("boolean")
    # document_type = 1
    # division = 1


class CuratedUrlFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CuratedUrl

    collection = factory.SubFactory(CollectionFactory)
    url = factory.Faker("url")
    scraped_title = factory.Faker("sentence")
    scraped_text = factory.Faker("paragraph")
    generated_title = factory.Faker("sentence")
    visited = factory.Faker("boolean")
    document_type = 1
    division = 1


class DeltaUrlFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DeltaUrl

    collection = factory.SubFactory(CollectionFactory)
    url = factory.Faker("url")
    scraped_title = factory.Faker("sentence")
    to_delete = False
