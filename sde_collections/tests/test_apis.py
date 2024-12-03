import pytest
from django.urls import reverse
from rest_framework import status

from sde_collections.tests.factories import (
    CollectionFactory,
    CuratedUrlFactory,
    DeltaUrlFactory,
)


@pytest.mark.django_db
class TestDeltaURLAPIView:
    """Test suite for the Delta URL API endpoints"""

    def setup_method(self):
        """Setup test data"""
        self.collection = CollectionFactory()

    def test_delta_url_api_empty_list(self, client):
        """Should return empty list when no delta URLs exist"""
        url = reverse("sde_collections:delta-url-api", kwargs={"config_folder": self.collection.config_folder})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["results"]) == 0

    def test_delta_url_api_with_data(self, client):
        """Should return list of non-excluded delta URLs for given config folder"""
        delta_url1 = DeltaUrlFactory(collection=self.collection)

        url = reverse("sde_collections:delta-url-api", kwargs={"config_folder": self.collection.config_folder})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["results"]
        assert len(data) == 1
        assert data[0]["url"] == delta_url1.url
        expected_title = delta_url1.generated_title if delta_url1.generated_title else delta_url1.scraped_title
        assert data[0]["title"] == expected_title

    def test_delta_url_api_wrong_config_folder(self, client):
        """Should return empty list for non-existent config folder"""
        url = reverse("sde_collections:delta-url-api", kwargs={"config_folder": "nonexistent"})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["results"]) == 0

    def test_delta_url_api_serializer_fields(self, client):
        """Should return all expected fields in serializer"""
        DeltaUrlFactory(collection=self.collection)

        url = reverse("sde_collections:delta-url-api", kwargs={"config_folder": self.collection.config_folder})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["results"][0]
        expected_fields = {"url", "title", "document_type", "file_extension", "tree_root"}
        assert set(data.keys()) == expected_fields

    def test_delta_url_api_pagination(self, client):
        """Should correctly paginate results when multiple URLs exist"""
        [DeltaUrlFactory(collection=self.collection) for _ in range(15)]

        url = reverse("sde_collections:delta-url-api", kwargs={"config_folder": self.collection.config_folder})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "next" in data
        assert "previous" in data
        assert "count" in data
        assert data["count"] == 15


@pytest.mark.django_db
class TestCuratedURLAPIView:
    """Test suite for the Curated URL API endpoints"""

    def setup_method(self):
        """Setup test data"""
        self.collection = CollectionFactory()

    def test_curated_url_api_empty_list(self, client):
        """Should return empty list when no curated URLs exist"""
        url = reverse("sde_collections:curated-url-api", kwargs={"config_folder": self.collection.config_folder})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["results"]) == 0

    def test_curated_url_api_with_data(self, client):
        """Should return list of curated URLs for given config folder"""
        curated_url1 = CuratedUrlFactory(collection=self.collection, generated_title="Test Generated Title")

        url = reverse("sde_collections:curated-url-api", kwargs={"config_folder": self.collection.config_folder})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["results"]
        assert len(data) == 1
        assert data[0]["url"] == curated_url1.url
        assert data[0]["title"] == curated_url1.generated_title

    def test_curated_url_api_wrong_config_folder(self, client):
        """Should return empty list for non-existent config folder"""
        url = reverse("sde_collections:curated-url-api", kwargs={"config_folder": "nonexistent"})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["results"]) == 0

    def test_curated_url_api_serializer_fields(self, client):
        """Should return all expected fields in serializer"""
        CuratedUrlFactory(collection=self.collection)

        url = reverse("sde_collections:curated-url-api", kwargs={"config_folder": self.collection.config_folder})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["results"][0]
        expected_fields = {"url", "title", "document_type", "file_extension", "tree_root"}
        assert set(data.keys()) == expected_fields

    def test_candidate_url_api_alias(self, client):
        """Should verify candidate-urls-api endpoint aliases to curated-urls-api"""
        curated_url = CuratedUrlFactory(collection=self.collection, generated_title="Test Generated Title")

        curated_url = reverse(
            "sde_collections:curated-url-api", kwargs={"config_folder": self.collection.config_folder}
        )
        candidate_url = reverse(
            "sde_collections:candidate-url-api", kwargs={"config_folder": self.collection.config_folder}
        )

        curated_response = client.get(curated_url)
        candidate_response = client.get(candidate_url)

        assert curated_response.status_code == status.HTTP_200_OK
        assert candidate_response.status_code == status.HTTP_200_OK
        assert curated_response.json()["results"] == candidate_response.json()["results"]

    def test_multiple_collections(self, client):
        """Should only return URLs from the specified collection"""
        other_collection = CollectionFactory()

        url1 = CuratedUrlFactory(collection=self.collection, generated_title="Test Generated Title 1")
        CuratedUrlFactory(collection=other_collection, generated_title="Test Generated Title 2")

        url = reverse("sde_collections:curated-url-api", kwargs={"config_folder": self.collection.config_folder})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["results"]
        assert len(data) == 1
        assert data[0]["url"] == url1.url
        assert data[0]["title"] == url1.generated_title

    def test_curated_url_api_invalid_filters(self, client):
        """Should handle invalid filter parameters gracefully"""
        CuratedUrlFactory(collection=self.collection)

        url = reverse("sde_collections:curated-url-api", kwargs={"config_folder": self.collection.config_folder})
        response = client.get(f"{url}?invalid_filter=value")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["results"]
        assert len(data) == 1


@pytest.mark.django_db
class TestCandidateURLAPIView:
    """Test suite for the Candidate URL API endpoints. Note that this is an alias for Curated URL API"""

    def setup_method(self):
        """Setup test data"""
        self.collection = CollectionFactory()

    def test_candidate_url_api_empty_list(self, client):
        """Should return empty list when no candidate URLs exist"""
        url = reverse("sde_collections:candidate-url-api", kwargs={"config_folder": self.collection.config_folder})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["results"]) == 0

    def test_candidate_url_api_with_data(self, client):
        """Should return list of candidate URLs for given config folder"""
        candidate_url1 = CuratedUrlFactory(collection=self.collection, generated_title="Test Generated Title")

        url = reverse("sde_collections:candidate-url-api", kwargs={"config_folder": self.collection.config_folder})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["results"]
        assert len(data) == 1
        assert data[0]["url"] == candidate_url1.url
        assert data[0]["title"] == candidate_url1.generated_title

    def test_candidate_url_api_wrong_config_folder(self, client):
        """Should return empty list for non-existent config folder"""
        url = reverse("sde_collections:candidate-url-api", kwargs={"config_folder": "nonexistent"})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["results"]) == 0

    def test_candidate_url_api_serializer_fields(self, client):
        """Should return all expected fields in serializer"""
        CuratedUrlFactory(collection=self.collection)

        url = reverse("sde_collections:candidate-url-api", kwargs={"config_folder": self.collection.config_folder})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["results"][0]
        expected_fields = {"url", "title", "document_type", "file_extension", "tree_root"}
        assert set(data.keys()) == expected_fields

    def test_candidate_url_api_alias(self, client):
        """Should verify candidate-urls-api endpoint aliases to candidate-urls-api"""
        candidate_url = CuratedUrlFactory(collection=self.collection, generated_title="Test Generated Title")

        candidate_url = reverse(
            "sde_collections:candidate-url-api", kwargs={"config_folder": self.collection.config_folder}
        )
        candidate_url = reverse(
            "sde_collections:candidate-url-api", kwargs={"config_folder": self.collection.config_folder}
        )

        candidate_response = client.get(candidate_url)
        candidate_response = client.get(candidate_url)

        assert candidate_response.status_code == status.HTTP_200_OK
        assert candidate_response.status_code == status.HTTP_200_OK
        assert candidate_response.json()["results"] == candidate_response.json()["results"]

    def test_multiple_collections(self, client):
        """Should only return URLs from the specified collection"""
        other_collection = CollectionFactory()

        url1 = CuratedUrlFactory(collection=self.collection, generated_title="Test Generated Title 1")
        CuratedUrlFactory(collection=other_collection, generated_title="Test Generated Title 2")

        url = reverse("sde_collections:candidate-url-api", kwargs={"config_folder": self.collection.config_folder})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["results"]
        assert len(data) == 1
        assert data[0]["url"] == url1.url
        assert data[0]["title"] == url1.generated_title

    def test_candidate_url_api_invalid_filters(self, client):
        """Should handle invalid filter parameters gracefully"""
        CuratedUrlFactory(collection=self.collection)

        url = reverse("sde_collections:candidate-url-api", kwargs={"config_folder": self.collection.config_folder})
        response = client.get(f"{url}?invalid_filter=value")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["results"]
        assert len(data) == 1
