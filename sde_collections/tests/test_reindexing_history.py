# docker-compose -f local.yml run --rm django pytest -s sde_collections/tests/test_reindexing_history.py

import pytest
from django.contrib.auth import get_user_model

from sde_collections.models.collection import ReindexingHistory
from sde_collections.models.collection_choice_fields import ReindexingStatusChoices
from sde_collections.tests.factories import CollectionFactory, UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestReindexingHistory:
    """Test suite for ReindexingHistory functionality"""

    def setup_method(self):
        """Setup test data"""
        self.collection = CollectionFactory()
        self.user1 = UserFactory()
        self.user2 = UserFactory()

    def test_reindexing_history_status_change(self):
        """Should create history entry when reindexing status changes"""
        self.collection.reindexing_status = ReindexingStatusChoices.REINDEXING_NEEDED_ON_DEV
        self.collection.save()

        history = ReindexingHistory.objects.filter(collection=self.collection)
        assert history.count() == 1
        assert history.first().reindexing_status == ReindexingStatusChoices.REINDEXING_NEEDED_ON_DEV
        assert history.first().old_status == ReindexingStatusChoices.REINDEXING_NOT_NEEDED

    def test_reindexing_history_curator_change(self):
        """Should create history entry when curator changes"""
        self.collection.reindexing_curated_by = self.user1
        self.collection.save()

        history = ReindexingHistory.objects.filter(collection=self.collection)
        assert history.count() == 1
        assert history.first().curated_by == self.user1
        assert history.first().old_curator is None

    def test_reindexing_history_both_changes(self):
        """Should create history entry when both status and curator change"""
        self.collection.reindexing_status = ReindexingStatusChoices.REINDEXING_NEEDED_ON_DEV
        self.collection.reindexing_curated_by = self.user1
        self.collection.save()

        history = ReindexingHistory.objects.filter(collection=self.collection)
        assert history.count() == 1
        entry = history.first()
        assert entry.reindexing_status == ReindexingStatusChoices.REINDEXING_NEEDED_ON_DEV
        assert entry.old_status == ReindexingStatusChoices.REINDEXING_NOT_NEEDED
        assert entry.curated_by == self.user1
        assert entry.old_curator is None

    def test_reindexing_history_multiple_changes(self):
        """Should create multiple history entries for sequential changes"""
        # First change
        self.collection.reindexing_status = ReindexingStatusChoices.REINDEXING_NEEDED_ON_DEV
        self.collection.reindexing_curated_by = self.user1
        self.collection.save()

        # Second change
        self.collection.reindexing_status = ReindexingStatusChoices.REINDEXING_FINISHED_ON_DEV
        self.collection.reindexing_curated_by = self.user2
        self.collection.save()

        history = ReindexingHistory.objects.filter(collection=self.collection).order_by("created_at")
        assert history.count() == 2

        first_entry = history[0]
        assert first_entry.reindexing_status == ReindexingStatusChoices.REINDEXING_NEEDED_ON_DEV
        assert first_entry.old_status == ReindexingStatusChoices.REINDEXING_NOT_NEEDED
        assert first_entry.curated_by == self.user1
        assert first_entry.old_curator is None

        second_entry = history[1]
        assert second_entry.reindexing_status == ReindexingStatusChoices.REINDEXING_FINISHED_ON_DEV
        assert second_entry.old_status == ReindexingStatusChoices.REINDEXING_NEEDED_ON_DEV
        assert second_entry.curated_by == self.user2
        assert second_entry.old_curator == self.user1
