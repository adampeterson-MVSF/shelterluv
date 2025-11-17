"""
Detailed medical parsing functions for ShelterLuv scraper.

Handles extraction of comprehensive medical data including vaccinations, treatments,
diagnoses, tests, exams, and procedures from the Complete Medical History page.
"""

from typing import Any, Dict
from .parsers_basic_info import (
    _extract_microchip_info_from_medical_history,
    _extract_previous_shelter_info_from_medical_history,
    _extract_weight_info_from_medical_history
)
from .parsers_medical_history import (
    _extract_vaccination_history,
    _extract_treatments_due,
    _extract_treatment_history,
    _extract_active_diagnoses,
    _extract_resolved_diagnoses,
    _extract_diagnostic_tests,
    _extract_physical_exams,
    _extract_procedures_surgeries
)


def _extract_medical_history(page, result: Dict[str, Any]) -> None:
    """Extract complete medical history including all sections."""
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

        # Extract detailed medical history sections
        _extract_vaccination_history(page, medical_data)
        _extract_treatments_due(page, medical_data)
        _extract_treatment_history(page, medical_data)
        _extract_active_diagnoses(page, medical_data)
        _extract_resolved_diagnoses(page, medical_data)
        _extract_diagnostic_tests(page, medical_data)
        _extract_physical_exams(page, medical_data)
        _extract_procedures_surgeries(page, medical_data)

        # Store medical data if any was found
        if any(medical_data.values()):
            result["MedicalHistory"] = medical_data

    except Exception as e:
        print(f"Error extracting medical history: {e}")


# All detailed extraction functions have been moved to parsers_medical_history.py
