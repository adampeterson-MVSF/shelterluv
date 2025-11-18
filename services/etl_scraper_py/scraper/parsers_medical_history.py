"""
Medical history parsing functions for ShelterLuv scraper.

Handles extraction of detailed medical history including vaccinations,
treatments, diagnoses, and procedures.
"""

from typing import Any, Dict, List

from .navigation import SELECTORS
from .parsers_fields import extract_text_by_selector, extract_text_by_selectors, extract_table_rows_as_dicts, normalize_date_string

# Configuration for all medical table extractions
# Each entry maps to a medical_data key and defines selectors and column mappings
MEDICAL_TABLE_CONFIG = {
    "vaccinations": {
        "selectors": [
            SELECTORS["vaccination_table"],
            ".vaccinations-table",
            ".vaccination-history table",
            "[data-vaccinations] table"
        ],
        "columns": [
            ".vaccination-name",
            ".vaccination-date",
            ".vaccination-status",
            ".lot-number",
            ".expiration-date",
            ".rabies-tag",
            ".source",
            ".route",
            ".site",
            ".vaccinated-by"
        ],
        "field_mapping": {
            "name": ["Name", "Vaccination"],
            "date": ["Date"],
            "status": ["Status"],
            "lot_number": ["Lot Number", "Lot"],
            "expiration_date": ["Expiration"],
            "rabies_tag_number": ["Rabies Tag"],
            "source": ["Source"],
            "route": ["Route"],
            "site": ["Site"],
            "vaccinated_by": ["Vaccinated By"]
        },
        "date_fields": ["date", "expiration_date"],
        "required_fields": ["name", "date"]
    },
    "treatments_due": {
        "selectors": [
            SELECTORS["treatments_due_table"],
            ".treatments-due table",
            ".due-treatments table",
            "[data-treatments-due] table"
        ],
        "columns": [".treatment-name", ".dosage", ".frequency", ".due-date"],
        "field_mapping": {
            "name": ["Treatment", "Name"],
            "dosage": ["Dosage"],
            "frequency": ["Frequency"],
            "due_date": ["Due Date"]
        },
        "date_fields": ["due_date"],
        "required_fields": ["name"]
    },
    "treatment_history": {
        "selectors": [
            SELECTORS["treatment_history_table"],
            ".treatment-history table",
            ".treatment-records table",
            "[data-treatment-history] table"
        ],
        "columns": [".treatment-name", ".dosage", ".frequency", ".start-date", ".end-date", ".notes"],
        "field_mapping": {
            "name": ["Treatment", "Name"],
            "dosage": ["Dosage"],
            "frequency": ["Frequency"],
            "start_date": ["Start Date"],
            "end_date": ["End Date"],
            "notes": ["Notes"]
        },
        "date_fields": ["start_date", "end_date"],
        "required_fields": ["name"]
    },
    "active_diagnoses": {
        "selectors": [
            SELECTORS["active_diagnoses_table"],
            ".active-diagnoses table",
            ".current-diagnoses table",
            "[data-active-diagnoses] table"
        ],
        "columns": [".condition", ".diagnosed-date", ".notes"],
        "field_mapping": {
            "condition": ["Condition", "Diagnosis"],
            "diagnosed_date": ["Diagnosed Date", "Date"],
            "notes": ["Notes"]
        },
        "date_fields": ["diagnosed_date"],
        "required_fields": ["condition"]
    },
    "resolved_diagnoses": {
        "selectors": [
            SELECTORS["resolved_diagnoses_table"],
            ".resolved-diagnoses table",
            ".past-diagnoses table",
            "[data-resolved-diagnoses] table"
        ],
        "columns": [".condition", ".diagnosed-date", ".resolved-date", ".notes"],
        "field_mapping": {
            "condition": ["Condition", "Diagnosis"],
            "diagnosed_date": ["Diagnosed Date"],
            "resolved_date": ["Resolved Date"],
            "notes": ["Notes"]
        },
        "date_fields": ["diagnosed_date", "resolved_date"],
        "required_fields": ["condition"]
    },
    "diagnostic_tests": {
        "selectors": [
            SELECTORS["diagnostic_tests_table"],
            ".diagnostic-tests table",
            ".lab-tests table",
            "[data-diagnostic-tests] table"
        ],
        "columns": [
            ".test-type", ".test-name", ".date", ".results",
            ".results-detail", ".test-by", ".veterinarian", ".notes"
        ],
        "field_mapping": {
            "test_type": ["Test Type"],
            "test_name": ["Test Name", "Test"],
            "date": ["Date"],
            "results": ["Results"],
            "results_detail": ["Results Detail"],
            "test_by": ["Test By"],
            "veterinarian": ["Veterinarian"],
            "notes": ["Notes"]
        },
        "date_fields": ["date"],
        "required_fields": ["test_name", "results"]
    },
    "physical_exams": {
        "selectors": [
            SELECTORS["physical_exams_table"],
            ".physical-exams table",
            ".exam-records table",
            "[data-physical-exams] table"
        ],
        "columns": [".exam-type", ".date-time", ".details"],
        "field_mapping": {
            "exam_type": ["Exam Type", "Type"],
            "date_time": ["Date/Time", "Date"],
            "details": ["Details"]
        },
        "date_fields": [],
        "required_fields": ["exam_type", "details"]
    },
    "procedures_surgeries": {
        "selectors": [
            SELECTORS["procedures_table"],
            ".procedures-surgeries table",
            ".surgical-procedures table",
            "[data-procedures] table"
        ],
        "columns": [".procedure-type", ".date-time", ".details"],
        "field_mapping": {
            "procedure_type": ["Procedure Type", "Type"],
            "date_time": ["Date/Time", "Date"],
            "details": ["Details"]
        },
        "date_fields": [],
        "required_fields": ["procedure_type", "details"]
    }
}


def extract_generic_medical_table(page, table_key: str, medical_data: Dict[str, Any]) -> None:
    """Generic function to extract medical table data using configuration."""
    config = MEDICAL_TABLE_CONFIG[table_key]

    try:
        # Try each selector until one works
        for table_sel in config["selectors"]:
            try:
                rows = extract_table_rows_as_dicts(page, table_sel, config["columns"])

                if rows:
                    for row in rows:
                        # Map row data to standardized fields
                        item = {}
                        for field_name, possible_keys in config["field_mapping"].items():
                            # Try each possible key until we find a value
                            for key in possible_keys:
                                if key in row and row[key]:
                                    item[field_name] = row[key]
                                    break
                            else:
                                # No value found, use empty string
                                item[field_name] = ""

                        # Normalize date fields
                        for date_field in config["date_fields"]:
                            if date_field in item:
                                item[date_field] = normalize_date_string(item[date_field])

                        # Only add if required fields are present
                        if any(item.get(field) for field in config["required_fields"]):
                            medical_data[table_key].append(item)

                    break  # Found data, stop trying other selectors

            except Exception:
                continue  # Try next selector

    except Exception as e:
        print(f"Error extracting {table_key}: {e}")


def _extract_medical_history(page, result: Dict[str, Any]) -> None:
    """Extract complete medical history including all sections."""
    # This function has been unified into parsers_medical.extract_medical_history
    # Keeping for backward compatibility but delegating to unified implementation
    from .parsers_medical import extract_medical_history
    extract_medical_history(page, result)


