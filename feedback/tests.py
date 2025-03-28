# docker compose -f local.yml run --rm django pytest feedback/tests.py

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from feedback.models import ContentCurationRequest, Feedback, FeedbackFormDropdown


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def dropdown_option(db):
    return FeedbackFormDropdown.objects.create(name="I need help or have a general question", display_order=1)


@pytest.fixture
def feedback_data(dropdown_option):
    return {
        "name": "Test User",
        "email": "test@example.com",
        "subject": "Test Subject",
        "comments": "Test Comments",
        "source": "TEST",
        "dropdown_option": dropdown_option.id,
    }


@pytest.fixture
def content_curation_data():
    return {
        "name": "Test User",
        "email": "test@example.com",
        "scientific_focus": "Biology",
        "data_type": "Genomics",
        "data_link": "https://example.com/data",
        "additional_info": "Extra details",
    }


@pytest.mark.django_db
class TestFeedbackFormDropdown:
    def test_dropdown_str_representation(self, dropdown_option):
        """Test string representation of dropdown options"""
        assert str(dropdown_option) == "I need help or have a general question"

    def test_dropdown_ordering(self):
        """Test that dropdown options are ordered by display_order"""
        dropdown1 = FeedbackFormDropdown.objects.create(name="First Option", display_order=1)
        dropdown2 = FeedbackFormDropdown.objects.create(name="Second Option", display_order=2)
        dropdowns = FeedbackFormDropdown.objects.all()
        assert dropdowns[0] == dropdown1
        assert dropdowns[1] == dropdown2


@pytest.mark.django_db
class TestFeedbackAPI:
    def test_get_dropdown_options(self, api_client, dropdown_option):
        """Test retrieving dropdown options"""
        url = reverse("feedback:feedback-form-dropdown-options-api")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == dropdown_option.name

    def test_create_feedback_success(self, api_client, feedback_data):
        """Test successful feedback creation"""
        url = reverse("feedback:contact-us-api")
        response = api_client.post(url, feedback_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Feedback.objects.count() == 1

    def test_create_feedback_invalid_email(self, api_client, feedback_data):
        """Test feedback creation with invalid email"""
        url = reverse("feedback:contact-us-api")
        feedback_data["email"] = "invalid-email"
        response = api_client.post(url, feedback_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data["error"]

    @pytest.mark.parametrize("field", ["name", "email", "subject", "comments"])
    def test_create_feedback_missing_required_fields(self, api_client, feedback_data, field):
        """Test feedback creation with missing required fields"""
        url = reverse("feedback:contact-us-api")
        feedback_data.pop(field)
        response = api_client.post(url, feedback_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert field in response.data["error"]

    def test_create_feedback_invalid_dropdown(self, api_client, feedback_data):
        """Test feedback creation with non-existent dropdown option"""
        url = reverse("feedback:contact-us-api")
        feedback_data["dropdown_option"] = 999
        response = api_client.post(url, feedback_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "dropdown_option" in response.data["error"]


@pytest.mark.django_db
class TestContentCurationRequestAPI:
    def test_create_request_success(self, api_client, content_curation_data):
        """Test successful content curation request creation"""
        url = reverse("feedback:content-curation-request-api")
        response = api_client.post(url, content_curation_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert ContentCurationRequest.objects.count() == 1

    def test_create_request_without_additional_info(self, api_client, content_curation_data):
        """Test request creation without optional additional info"""
        url = reverse("feedback:content-curation-request-api")
        del content_curation_data["additional_info"]
        response = api_client.post(url, content_curation_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert ContentCurationRequest.objects.first().additional_info == ""

    def test_create_request_invalid_email(self, api_client, content_curation_data):
        """Test request creation with invalid email"""
        url = reverse("feedback:content-curation-request-api")
        content_curation_data["email"] = "invalid-email"
        response = api_client.post(url, content_curation_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data["error"]

    @pytest.mark.parametrize("field", ["name", "email", "scientific_focus", "data_type", "data_link"])
    def test_create_request_missing_required_fields(self, api_client, content_curation_data, field):
        """Test request creation with missing required fields"""
        url = reverse("feedback:content-curation-request-api")
        content_curation_data.pop(field)
        response = api_client.post(url, content_curation_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert field in response.data["error"]

    @pytest.mark.parametrize(
        "field,length", [("name", 151), ("data_link", 1001), ("scientific_focus", 201), ("data_type", 101)]
    )
    def test_create_request_field_max_lengths(self, api_client, content_curation_data, field, length):
        """Test request creation with fields exceeding max length"""
        url = reverse("feedback:content-curation-request-api")
        content_curation_data[field] = "x" * length
        response = api_client.post(url, content_curation_data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert field in response.data["error"]
