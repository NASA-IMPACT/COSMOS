# docker-compose -f local.yml run --rm django pytest environmental_justice/tests/test_views.py
import pytest
from rest_framework import status

from environmental_justice.models import EnvironmentalJusticeRow
from environmental_justice.tests.factories import EnvironmentalJusticeRowFactory


@pytest.mark.django_db
class TestEnvironmentalJusticeRowViewSet:
    """Test suite for the EnvironmentalJusticeRow API endpoints"""

    def setup_method(self):
        """Setup URL for API endpoint"""
        self.url = "/api/environmental-justice/"

    def test_empty_database_returns_empty_list(self, client):
        """Should return empty list when no records exist"""
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["results"] == []
        assert response.json()["count"] == 0

    def test_single_source_filtering(self, client):
        """Should return records only from requested data source"""
        # Create records for each data source
        spreadsheet_record = EnvironmentalJusticeRowFactory(
            dataset="test_dataset", data_source=EnvironmentalJusticeRow.DataSourceChoices.SPREADSHEET
        )
        ml_prod_record = EnvironmentalJusticeRowFactory(
            dataset="another_dataset", data_source=EnvironmentalJusticeRow.DataSourceChoices.ML_PRODUCTION
        )
        ml_test_record = EnvironmentalJusticeRowFactory(
            dataset="test_dataset_3", data_source=EnvironmentalJusticeRow.DataSourceChoices.ML_TESTING
        )

        # Test spreadsheet filter
        response = client.get(f"{self.url}?data_source=spreadsheet")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["results"]
        assert len(data) == 1
        assert data[0]["dataset"] == spreadsheet_record.dataset

        # Test ml_production filter
        response = client.get(f"{self.url}?data_source=ml_production")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["results"]
        assert len(data) == 1
        assert data[0]["dataset"] == ml_prod_record.dataset

        # Test ml_testing filter
        response = client.get(f"{self.url}?data_source=ml_testing")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["results"]
        assert len(data) == 1
        assert data[0]["dataset"] == ml_test_record.dataset

    def test_combined_data_precedence(self, client):
        """
        Should return combined data with spreadsheet taking precedence over ml_production
        for matching datasets
        """
        # Create spreadsheet record
        EnvironmentalJusticeRowFactory(
            dataset="common_dataset",
            description="spreadsheet version",
            data_source=EnvironmentalJusticeRow.DataSourceChoices.SPREADSHEET,
        )

        # Create ML production record with same dataset
        EnvironmentalJusticeRowFactory(
            dataset="common_dataset",
            description="ml version",
            data_source=EnvironmentalJusticeRow.DataSourceChoices.ML_PRODUCTION,
        )

        # Create unique ML production record
        EnvironmentalJusticeRowFactory(
            dataset="unique_ml_dataset", data_source=EnvironmentalJusticeRow.DataSourceChoices.ML_PRODUCTION
        )

        # Test combined view (default)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["results"]
        assert len(data) == 2  # Should only return 2 records (not 3)

        # Verify correct records are returned
        datasets = [record["dataset"] for record in data]
        assert "common_dataset" in datasets
        assert "unique_ml_dataset" in datasets

        # Verify precedence - should get spreadsheet version of common dataset
        common_record = next(r for r in data if r["dataset"] == "common_dataset")
        assert common_record["description"] == "spreadsheet version"

    def test_combined_explicit_parameter(self, client):
        """Should handle explicit 'combined' parameter same as default"""
        EnvironmentalJusticeRowFactory(data_source=EnvironmentalJusticeRow.DataSourceChoices.SPREADSHEET)
        EnvironmentalJusticeRowFactory(
            dataset="unique_ml_dataset",  # Ensure different dataset
            data_source=EnvironmentalJusticeRow.DataSourceChoices.ML_PRODUCTION,
        )

        # Compare default and explicit combined responses
        default_response = client.get(self.url)
        combined_response = client.get(f"{self.url}?data_source=combined")

        assert default_response.status_code == status.HTTP_200_OK
        assert combined_response.status_code == status.HTTP_200_OK
        assert default_response.json()["results"] == combined_response.json()["results"]

    def test_invalid_data_source(self, client):
        """Should return 400 error for invalid data_source parameter"""
        response = client.get(f"{self.url}?data_source=invalid")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid data_source" in str(response.json())

    def test_sorting_in_combined_view(self, client):
        """Should return combined results sorted by dataset name"""
        # Create records in non-alphabetical order
        EnvironmentalJusticeRowFactory(
            dataset="zebra_dataset", data_source=EnvironmentalJusticeRow.DataSourceChoices.SPREADSHEET
        )
        EnvironmentalJusticeRowFactory(
            dataset="alpha_dataset", data_source=EnvironmentalJusticeRow.DataSourceChoices.ML_PRODUCTION
        )

        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()["results"]

        # Verify sorting
        datasets = [record["dataset"] for record in data]
        assert datasets == sorted(datasets)

    def test_http_methods_allowed(self, client):
        """Should only allow GET requests"""
        # Test GET (should work)
        get_response = client.get(self.url)
        assert get_response.status_code == status.HTTP_200_OK

        # Test POST (should fail)
        post_response = client.post(self.url, {})
        assert post_response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # Test PUT (should fail)
        put_response = client.put(self.url, {})
        assert put_response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # Test DELETE (should fail)
        delete_response = client.delete(self.url)
        assert delete_response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
