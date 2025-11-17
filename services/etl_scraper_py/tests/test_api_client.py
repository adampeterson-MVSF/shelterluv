"""
Tests for API client functions in api_client.py.
Critical functions: get_all_animals_in_custody, get_animal_events, get_people.
Tests pagination logic, error handling, and data filtering.
"""

from unittest.mock import Mock, patch

import pytest

from api import (
    MAX_RETRIES,
    REQUEST_TIMEOUT,
    MemoResult,
    get_all_animals_in_custody,
    get_animal_by_internal_id,
    get_animal_events,
    get_animal_memos,
    get_animals_by_ids,
    get_animals_memos_batch,
    get_people,
)
from errors import ApiError


class TestGetAllAnimalsInCustody:
    """Test get_all_animals_in_custody function - most critical for data completeness."""

    @patch("api.api_client_base.requests.get")
    def test_get_all_animals_single_page(self, mock_get):
        """Test fetching animals from single page."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "animals": [
                {"Internal-ID": "1", "Name": "Dog1", "Status": "Headquarters Available"},
                {"Internal-ID": "2", "Name": "Dog2", "Status": "Foster Available"},
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_all_animals_in_custody("test-api-key")

        assert len(result) == 2
        assert result[0]["Internal-ID"] == "1"
        assert result[1]["Internal-ID"] == "2"

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]["headers"]["X-API-Key"] == "test-api-key"
        assert call_args[1]["params"] == {
            "page": 1,
            "per_page": 100,
            "include": "Internal-ID,Name,Status,ID,IntakeDate,Location,Stage,Breed,Gender,Size,Weight,Age",
        }

    @patch("api.api_client_base.requests.get")
    def test_get_all_animals_multiple_pages(self, mock_get):
        """Test fetching animals across multiple pages."""
        # First page response (100 animals triggers second page)
        first_response = Mock()
        first_response.json.return_value = {
            "animals": [
                {"Internal-ID": str(i), "Name": f"Dog{i}", "Status": "Headquarters Available"}
                for i in range(1, 101)  # 100 animals
            ]
        }
        first_response.raise_for_status.return_value = None

        # Second page response
        second_response = Mock()
        second_response.json.return_value = {
            "animals": [{"Internal-ID": "101", "Name": "Dog101", "Status": "Foster Available"}]
        }
        second_response.raise_for_status.return_value = None

        mock_get.side_effect = [first_response, second_response]

        result = get_all_animals_in_custody("test-api-key")

        assert len(result) == 101  # All animals pass the in-custody filter
        assert result[0]["Internal-ID"] == "1"
        assert result[1]["Internal-ID"] == "2"

        assert mock_get.call_count == 2

    @patch("api.api_client_base.requests.get")
    def test_get_all_animals_filters_custody_status(self, mock_get):
        """Test that only animals in custody are returned."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "animals": [
                {"Internal-ID": "1", "Name": "HeadquartersDog", "Status": "Headquarters Available"},
                {"Internal-ID": "2", "Name": "FosterDog", "Status": "Foster Available"},
                {
                    "Internal-ID": "3",
                    "Name": "PendingDog",
                    "Status": "Headquarters Unavailable - Pending Medical Exam",
                },
                {"Internal-ID": "4", "Name": "AdoptedDog", "Status": "ADOPTED"},
                {"Internal-ID": "5", "Name": "UnknownDog", "Status": "SOMETHING_ELSE"},
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_all_animals_in_custody("test-api-key")

        # Should exclude only specific statuses (ADOPTED, Transferred Out, etc.)
        # Based on current filtering logic: excludes {"Transferred Out", "Serviced Out", "ADOPTED", "Deceased"}
        assert len(result) == 4  # All except the ADOPTED one
        internal_ids = {dog["Internal-ID"] for dog in result}
        assert internal_ids == {"1", "2", "3", "5"}  # Excludes "4" (ADOPTED)

    @patch("api.api_client_base.requests.get")
    def test_get_all_animals_max_limit_enforced(self, mock_get):
        """Test that max_animals limit is enforced."""
        max_animals = 100  # Test with a smaller limit
        mock_response = Mock()
        # Create more animals than the limit
        animals = [
            {"Internal-ID": str(i), "Name": f"Dog{i}", "Status": "Headquarters Available"}
            for i in range(max_animals + 1)
        ]
        mock_response.json.return_value = {"animals": animals}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with pytest.raises(ApiError, match=f"Hit {max_animals}-animal cap"):
            get_all_animals_in_custody("test-api-key", max_animals=max_animals)

    @patch("api.api_client_base.requests.get")
    def test_get_all_animals_missing_internal_id(self, mock_get):
        """Test error when animal is missing Internal-ID."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "animals": [
                {"Name": "DogWithoutID", "Status": "Headquarters Available"},  # Missing Internal-ID
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with pytest.raises(ApiError, match="Animal missing required Internal-ID"):
            get_all_animals_in_custody("test-api-key")

    @patch("api.api_client_base.requests.get")
    def test_get_all_animals_http_error(self, mock_get):
        """Test handling of HTTP errors."""
        import requests

        mock_get.side_effect = requests.exceptions.RequestException("Connection failed")

        with pytest.raises(ApiError, match="ShelterLuv API request failed"):
            get_all_animals_in_custody("test-api-key")

    @patch("api.api_client_base.requests.get")
    def test_get_all_animals_timeout_error(self, mock_get):
        """Test handling of timeout errors."""
        import requests

        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        with pytest.raises(ApiError, match="ShelterLuv API request failed"):
            get_all_animals_in_custody("test-api-key")


class TestGetAnimalEvents:
    """Test get_animal_events function."""

    @patch("api.api_client_base.requests.get")
    def test_get_animal_events_filters_relevant_types(self, mock_get):
        """Test that only relevant event types are returned."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "events": [
                {"Type": "Foster", "Date": "2023-01-01", "AnimalID": "1"},
                {"Type": "FosterReturn", "Date": "2023-01-02", "AnimalID": "1"},
                {"Type": "Event", "Date": "2023-01-03", "AnimalID": "1"},
                {"Type": "Adoption", "Date": "2023-01-04", "AnimalID": "1"},
                {"Type": "Intake", "Date": "2023-01-05", "AnimalID": "1"},
                {
                    "Type": "Irrelevant",
                    "Date": "2023-01-06",
                    "AnimalID": "1",
                },  # Should be filtered out
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_animal_events("test-api-key")

        assert (
            len(result) == 5
        )  # Foster, FosterReturn, Event, Adoption, Intake (Irrelevant filtered out)
        event_types = {event["Type"] for event in result}
        assert event_types == {"Foster", "FosterReturn", "Event", "Adoption", "Intake"}

    @patch("api.api_client_base.requests.get")
    def test_get_animal_events_sorts_chronologically(self, mock_get):
        """Test that events are sorted chronologically."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "events": [
                {"Type": "Foster", "Date": "2023-01-03", "AnimalID": "1"},
                {"Type": "Foster", "Date": "2023-01-01", "AnimalID": "1"},
                {"Type": "Event", "Date": "2023-01-02", "AnimalID": "1"},
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_animal_events("test-api-key")

        assert len(result) == 3
        # Should be sorted by date
        assert result[0]["Date"] == "2023-01-01"
        assert result[1]["Date"] == "2023-01-02"
        assert result[2]["Date"] == "2023-01-03"

    @patch("api.api_client_base.requests.get")
    def test_get_animal_events_pagination(self, mock_get):
        """Test pagination handling for events."""
        # First page (full page of 100 events triggers second page request)
        first_response = Mock()
        first_response.json.return_value = {
            "events": [{"Type": "Foster", "Date": "2023-01-01", "AnimalID": "1"}] * 100
        }
        first_response.raise_for_status.return_value = None

        # Second page (partial page ends pagination)
        second_response = Mock()
        second_response.json.return_value = {
            "events": [{"Type": "Event", "Date": "2023-01-02", "AnimalID": "2"}]
        }
        second_response.raise_for_status.return_value = None

        mock_get.side_effect = [first_response, second_response]

        result = get_animal_events("test-api-key")

        assert len(result) == 101  # 100 from first page + 1 from second page
        assert mock_get.call_count == 2

    @patch("api.api_client_base.requests.get")
    def test_get_animal_events_http_error(self, mock_get):
        """Test handling of HTTP errors in events API."""
        import requests

        mock_get.side_effect = requests.exceptions.RequestException("Connection failed")

        with pytest.raises(ApiError, match="ShelterLuv API request failed after 3 attempts"):
            get_animal_events("test-api-key")


class TestGetPeople:
    """Test get_people function."""

    @patch("api.api_client_base.requests.get")
    def test_get_people_basic_fetch(self, mock_get):
        """Test basic people fetching."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "people": [
                {"ID": "1", "Name": "John Doe", "Email": "john@example.com"},
                {"ID": "2", "Name": "Jane Smith", "Email": "jane@example.com"},
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_people("test-api-key")

        assert len(result) == 2
        assert result[0]["Name"] == "John Doe"
        assert result[1]["Name"] == "Jane Smith"

    @patch("api.api_client_base.requests.get")
    def test_get_people_pagination(self, mock_get):
        """Test pagination handling for people."""
        # First page (full page of 100 people triggers second page request)
        first_response = Mock()
        first_response.json.return_value = {
            "people": [{"ID": str(i), "Name": f"Person{i}"} for i in range(1, 101)]
        }
        first_response.raise_for_status.return_value = None

        # Second page (partial page ends pagination)
        second_response = Mock()
        second_response.json.return_value = {"people": [{"ID": "101", "Name": "Person101"}]}
        second_response.raise_for_status.return_value = None

        mock_get.side_effect = [first_response, second_response]

        result = get_people("test-api-key")

        assert len(result) == 101  # 100 from first page + 1 from second page
        assert mock_get.call_count == 2

    @patch("api.api_client_base.requests.get")
    def test_get_people_http_error(self, mock_get):
        """Test handling of HTTP errors in people API."""
        import requests

        mock_get.side_effect = requests.exceptions.RequestException("Connection failed")

        with pytest.raises(ApiError, match="ShelterLuv API request failed after 3 attempts"):
            get_people("test-api-key")


class TestGetAnimalMemos:
    """Test get_animal_memos function."""

    @patch("api.api_client_base.requests.get")
    def test_get_animal_memos_success_with_documents(self, mock_get):
        """Test successful retrieval of memos from documents endpoint."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "documents": [
                {"type": "memo", "content": "Medical note: healthy dog"},
                {"type": "other", "content": "Some other document"},
                {"type": "memo", "content": "Behavior note: friendly"},
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_animal_memos("test-api-key", "123")

        expected = MemoResult(
            internal_id="123",
            memos_html="Medical note: healthy dog<br>Behavior note: friendly",
            source="api",
            api_failed=False,
        )
        assert result == expected
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]["headers"]["X-API-Key"] == "test-api-key"
        assert call_args[0][0] == "https://new.shelterluv.com/api/v1/animals/123/memos"

    @patch("api.api_client_base.requests.get")
    def test_get_animal_memos_success_with_memos_field(self, mock_get):
        """Test successful retrieval when memos are in a direct memos field."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "memos": [
                {"Content": "Intake note: found as stray"},
                {"Content": "Medical note: vaccinated"},
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_animal_memos("test-api-key", "123")

        expected = MemoResult(
            internal_id="123",
            memos_html="Intake note: found as stray<br>Medical note: vaccinated",
            source="api",
            api_failed=False,
        )
        assert result == expected

    @patch("api.api_client_base.requests.get")
    def test_get_animal_memos_success_with_string_memos(self, mock_get):
        """Test successful retrieval when memos is a string field."""
        mock_response = Mock()
        mock_response.json.return_value = {"memos": "Single memo content"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_animal_memos("test-api-key", "123")

        expected = MemoResult(
            internal_id="123", memos_html="Single memo content", source="api", api_failed=False
        )
        assert result == expected

    @patch("api.api_client_base.requests.get")
    def test_get_animal_memos_empty_response(self, mock_get):
        """Test handling of response with no memos."""
        mock_response = Mock()
        mock_response.json.return_value = {"documents": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_animal_memos("test-api-key", "123")

        expected = MemoResult(internal_id="123", memos_html="", source="api", api_failed=False)
        assert result == expected

    @patch("api.api_client_base.requests.get")
    def test_get_animal_memos_api_error(self, mock_get):
        """Test graceful handling of API errors."""
        import requests

        mock_get.side_effect = requests.exceptions.RequestException("API down")

        result = get_animal_memos("test-api-key", "123")

        expected = MemoResult(internal_id="123", memos_html="", source="api", api_failed=True)
        assert result == expected


class TestGetAnimalsMemosBatch:
    """Test get_animals_memos_batch function."""

    # @patch('api_client_memos.get_animal_memos')
    # def test_get_animals_memos_batch_success(self, mock_individual):
    #     """Test successful batch retrieval of memos."""
    #     mock_individual.side_effect = [
    #         MemoResult(internal_id="123", memos_html="Medical note for dog 123<br>Behavior note for dog 123", source="api", api_failed=False),
    #         MemoResult(internal_id="456", memos_html="Single memo for dog 456", source="api", api_failed=False),
    #         MemoResult(internal_id="789", memos_html="", source="api", api_failed=False)
    #     ]

    #     result = get_animals_memos_batch("test-api-key", ["123", "456", "789"])

    #     expected = {
    #         "123": MemoResult(internal_id="123", memos_html="Medical note for dog 123<br>Behavior note for dog 123", source="api", api_failed=False),
    #         "456": MemoResult(internal_id="456", memos_html="Single memo for dog 456", source="api", api_failed=False),
    #         "789": MemoResult(internal_id="789", memos_html="", source="api", api_failed=False)
    #     }
    #     assert result == expected

    @patch("api.api_client_base.requests.get")
    def test_get_animals_memos_batch_empty_list(self, mock_get):
        """Test batch retrieval with empty input list."""
        result = get_animals_memos_batch("test-api-key", [])

        assert result == {}

    @patch("api.api_client_memos.get_animal_memos")
    def test_get_animals_memos_batch_concurrent_success(self, mock_individual):
        """Test successful batch retrieval using concurrent individual calls."""
        mock_individual.side_effect = [
            MemoResult(
                internal_id="123", memos_html="Memo for 123", source="api", api_failed=False
            ),
            MemoResult(
                internal_id="456", memos_html="Memo for 456", source="api", api_failed=False
            ),
            MemoResult(internal_id="789", memos_html="", source="api", api_failed=False),
        ]

        result = get_animals_memos_batch("test-api-key", ["123", "456", "789"])

        expected = {
            "123": MemoResult(
                internal_id="123", memos_html="Memo for 123", source="api", api_failed=False
            ),
            "456": MemoResult(
                internal_id="456", memos_html="Memo for 456", source="api", api_failed=False
            ),
            "789": MemoResult(internal_id="789", memos_html="", source="api", api_failed=False),
        }
        assert result == expected

        # Should have called get_animal_memos for each ID
        assert mock_individual.call_count == 3
