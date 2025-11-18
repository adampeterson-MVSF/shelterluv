"""
Comprehensive medical parsing functions for ShelterLuv scraper.

Handles extraction of complete medical history including vaccinations, treatments,
diagnoses, tests, exams, procedures, and additional basic info.
"""

from typing import Any, Dict
from .parsers_basic_info import (
    _extract_microchip_info_from_medical_history,
    _extract_previous_shelter_info_from_medical_history,
    _extract_weight_info_from_medical_history
)
from .parsers_medical_history import (
    MEDICAL_TABLE_CONFIG,
    extract_generic_medical_table
)


def extract_medical_history(page, result: Dict[str, Any]) -> None:
    """Extract complete medical history including all sections and basic info."""
    try:
        # Initialize medical data structure
        medical_data = {
            "vaccinations": [],
            "treatments_due": [],
            "treatment_history": [],
            "active_diagnoses": [],
            "resolved_diagnoses": [],
            "diagnostic_tests": [],
            "physical_exams": [],
            "procedures_surgeries": []
        }

        # Extract basic info from medical history tables
        _extract_microchip_info_from_medical_history(page, result)
        _extract_previous_shelter_info_from_medical_history(page, result)
        _extract_weight_info_from_medical_history(page, result)

        # Extract detailed medical history sections using configuration
        for table_key in MEDICAL_TABLE_CONFIG.keys():
            extract_generic_medical_table(page, table_key, medical_data)

        # Store medical data if any was found
        if any(medical_data.values()):
            result["MedicalHistory"] = medical_data

    except Exception as e:
        print(f"Error extracting medical history: {e}")