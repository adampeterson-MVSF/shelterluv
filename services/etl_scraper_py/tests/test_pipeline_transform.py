"""
Tests for pipeline transform phase - data processing and normalization.
Tests that transform correctly processes scraped data from extract phase.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from config import EnvProfile, EtlConfig, SecretsConfig, SecretsMode
from errors import ApiError
from pipeline import (
    ExtractResult,
    TransformConfig,
    TransformResult,
)
from transform import transform


class TestIncrementalScraping:
    """Test incremental ETL functionality within transform."""

    def test_transform_processes_scraped_data(self):
        """Test that transform processes data that was scraped in extract phase."""
        # Setup extract result with scraped data (simulating what extract phase would produce)
        extract_result = ExtractResult(
            in_custody_ids={"1", "2"},
            animals_by_id={
                "1": {
                    "Internal-ID": "1",
                    "ID": "A1",
                    "Name": "Dog 1",
                    "Status": "AVAILABLE",
                    "AgeYears": 2.0,
                    "AgeDisplay": "2 years",
                    "IsInCustody": True,
                    "IsAvailableForAdoption": True,
                    "IsHospice": False,
                    "IsEventDog": False,
                    "SourceUpdatedAt": "2024-01-01T10:00:00Z",
                },
                "2": {
                    "Internal-ID": "2",
                    "ID": "A2",
                    "Name": "Dog 2",
                    "Status": "AVAILABLE",
                    "AgeYears": 3.0,
                    "AgeDisplay": "3 years",
                    "IsInCustody": True,
                    "IsAvailableForAdoption": True,
                    "IsHospice": False,
                    "IsEventDog": False,
                    "SourceUpdatedAt": "2024-01-01T11:00:00Z",
                },
            },
            events=[{"event": "test"}],
            people=[{"person": "test"}],
            existing_metadata={},
            memos_data={},
            scraped_map={
                "1": {
                    "Internal-ID": "1",
                    "Name": "Dog 1 Scraped",
                    "Breed": "Golden Retriever",
                    "Size": "Large",
                    "Color": "Golden",
                    "MedicalHistory": ["Vaccinated"],
                    "BehaviorNotes": "Friendly",
                },
                "2": {
                    "Internal-ID": "2",
                    "Name": "Dog 2 Scraped",
                    "Breed": "Labrador",
                    "Size": "Medium",
                    "Color": "Black",
                    "MedicalHistory": ["Spayed"],
                    "BehaviorNotes": "Energetic",
                },
            },
        )

        # Setup transform config
        transform_config = TransformConfig()
        creds = {"SHELTERLUV_USERNAME": "test", "SHELTERLUV_PASSWORD": "test"}

        # Run transform
        result = transform(extract_result, creds, transform_config)

        # Assertions
        assert isinstance(result, TransformResult)
        assert len(result.dogs) == 2

        # Check that scraped data was merged with API data
        dog1 = next(d for d in result.dogs if d["Internal-ID"] == "1")
        dog2 = next(d for d in result.dogs if d["Internal-ID"] == "2")

        # API data should be preserved
        assert dog1["ID"] == "A1"
        assert dog1["Status"] == "AVAILABLE"
        assert dog1["AgeYears"] == 2.0
        assert dog1["AgeDisplay"] == "2 years"

        # Scraped data should be added
        assert dog1["Breed"] == "Golden Retriever"
        assert dog1["Size"] == "Large"
        assert dog1["Color"] == "Golden"
        assert dog1["MedicalHistory"] == ["Vaccinated"]
        assert dog1["BehaviorNotes"] == "Friendly"

        # Same for dog 2
        assert dog2["ID"] == "A2"
        assert dog2["Breed"] == "Labrador"
        assert dog2["Size"] == "Medium"
        assert dog2["Color"] == "Black"
        assert dog2["MedicalHistory"] == ["Spayed"]
        assert dog2["BehaviorNotes"] == "Energetic"

    def test_transform_processes_all_scraped_data(self):
        """Test that transform processes all scraped data when available."""
        # Setup with more comprehensive scraped data
        extract_result = ExtractResult(
            in_custody_ids={"1"},
            animals_by_id={
                "1": {
                    "Internal-ID": "1",
                    "ID": "A1",
                    "Name": "Dog 1",
                    "Status": "AVAILABLE",
                    "AgeYears": 1.5,
                    "AgeDisplay": "1.5 years",
                    "IsInCustody": True,
                    "IsAvailableForAdoption": True,
                    "IsHospice": False,
                    "IsEventDog": False,
                    "SourceUpdatedAt": "2024-01-01T10:00:00Z",
                },
            },
            events=[],
            people=[],
            existing_metadata={},
            memos_data={},
            scraped_map={
                "1": {
                    "Internal-ID": "1",
                    "Name": "Dog 1 Scraped",
                    "Breed": "Mixed",
                    "Size": "Medium",
                    "Color": "Brown/White",
                    "Sex": "Female",
                    "WeightLbs": 45.0,
                    "MedicalHistory": ["Vaccinated", "Spayed"],
                    "BehaviorNotes": "Good with kids",
                    "Categories": ["Family Dog", "Medium Energy"],
                    "Photos": ["photo1.jpg", "photo2.jpg"],
                    "Memos": "Adopted from another shelter",
                    "IntakeDate": "2023-06-01",
                    "OutcomeDate": None,
                },
            },
        )

        transform_config = TransformConfig()
        creds = {"SHELTERLUV_USERNAME": "test", "SHELTERLUV_PASSWORD": "test"}

        result = transform(extract_result, creds, transform_config)

        assert len(result.dogs) == 1
        dog = result.dogs[0]

        # All fields should be present
        assert dog["Internal-ID"] == "1"
        assert dog["ID"] == "A1"
        assert dog["Name"] == "Dog 1"
        assert dog["Status"] == "AVAILABLE"
        assert dog["Breed"] == "Mixed"
        assert dog["Size"] == "Medium"
        assert dog["Color"] == "Brown/White"
        assert dog["Sex"] == "Female"
        assert dog["WeightLbs"] == 45.0
        assert dog["MedicalHistory"] == ["Vaccinated", "Spayed"]
        assert dog["BehaviorNotes"] == "Good with kids"
        assert dog["Categories"] == ["Family Dog", "Medium Energy"]
        assert dog["Photos"] == ["photo1.jpg", "photo2.jpg"]
        assert dog["Memos"] == "Adopted from another shelter"
        assert dog["IntakeDate"] == "2023-06-01"
        assert dog["OutcomeDate"] is None

    def test_transform_processes_many_dogs(self):
        """Test transform handles many dogs efficiently."""
        # Create 100 dogs with scraped data
        num_dogs = 100
        in_custody_ids = {str(i) for i in range(1, num_dogs + 1)}

        animals_by_id = {}
        scraped_map = {}

        for i in range(1, num_dogs + 1):
            dog_id = str(i)
            animals_by_id[dog_id] = {
                "Internal-ID": dog_id,
                "ID": f"A{dog_id}",
                "Name": f"Dog {dog_id}",
                "Status": "AVAILABLE",
                "AgeYears": 2.0,
                "AgeDisplay": "2 years",
                "IsInCustody": True,
                "IsAvailableForAdoption": True,
                "IsHospice": False,
                "IsEventDog": False,
                "SourceUpdatedAt": "2024-01-01T10:00:00Z",
            }
            scraped_map[dog_id] = {
                "Internal-ID": dog_id,
                "Name": f"Dog {dog_id} Scraped",
                "Breed": "Mixed",
                "Size": "Medium",
                "MedicalHistory": ["Vaccinated"],
            }

        extract_result = ExtractResult(
            in_custody_ids=in_custody_ids,
            animals_by_id=animals_by_id,
            events=[],
            people=[],
            existing_metadata={},
            memos_data={},
            scraped_map=scraped_map,
        )

        transform_config = TransformConfig()
        creds = {"SHELTERLUV_USERNAME": "test", "SHELTERLUV_PASSWORD": "test"}

        result = transform(extract_result, creds, transform_config)

        # All dogs should be processed
        assert len(result.dogs) == num_dogs

        # Check a few dogs to ensure data integrity
        for i in [1, 50, 100]:
            dog = next(d for d in result.dogs if d["Internal-ID"] == str(i))
            assert dog["ID"] == f"A{i}"
            assert dog["Name"] == f"Dog {i}"
            assert dog["Breed"] == "Mixed"
            assert dog["Size"] == "Medium"
            assert dog["MedicalHistory"] == ["Vaccinated"]

        # Scraping is now done in extract phase, not transform
