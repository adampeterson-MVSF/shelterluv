"""
Medical history parsing functions for ShelterLuv scraper.

Handles extraction of detailed medical history including vaccinations,
treatments, diagnoses, and procedures.
"""

from typing import Any, Dict, List

from .navigation import SELECTORS
from .parsers_fields import extract_text_by_selector, extract_text_by_selectors, extract_table_rows_as_dicts, normalize_date_string


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

        # Extract vaccination history
        _extract_vaccination_history(page, medical_data)

        # Extract treatments due
        _extract_treatments_due(page, medical_data)

        # Extract treatment history
        _extract_treatment_history(page, medical_data)

        # Extract active diagnoses
        _extract_active_diagnoses(page, medical_data)

        # Extract resolved diagnoses
        _extract_resolved_diagnoses(page, medical_data)

        # Extract diagnostic tests
        _extract_diagnostic_tests(page, medical_data)

        # Extract physical exams
        _extract_physical_exams(page, medical_data)

        # Extract procedures/surgeries
        _extract_procedures_surgeries(page, medical_data)

        # Store medical data in result
        result["MedicalHistory"] = medical_data

    except Exception as e:
        print(f"Error extracting medical history: {e}")


def _extract_vaccination_history(page, medical_data: Dict[str, Any]) -> None:
    """Extract vaccination history from medical records."""
    try:
        # Look for vaccination table
        vaccination_table_selectors = [
            SELECTORS.vaccination_table,
            ".vaccinations-table",
            ".vaccination-history table",
            "[data-vaccinations] table"
        ]

        for table_sel in vaccination_table_selectors:
            try:
                rows = extract_table_rows_as_dicts(
                    page,
                    table_sel,
                    [
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
                    ]
                )

                if rows:
                    for row in rows:
                        vaccination = {
                            "name": row.get("Name", row.get("Vaccination", "")),
                            "date": normalize_date_string(row.get("Date", "")),
                            "status": row.get("Status", ""),
                            "lot_number": row.get("Lot Number", row.get("Lot", "")),
                            "expiration_date": normalize_date_string(row.get("Expiration", "")),
                            "rabies_tag_number": row.get("Rabies Tag", ""),
                            "source": row.get("Source", ""),
                            "route": row.get("Route", ""),
                            "site": row.get("Site", ""),
                            "vaccinated_by": row.get("Vaccinated By", "")
                        }
                        if vaccination["name"] or vaccination["date"]:
                            medical_data["vaccinations"].append(vaccination)
                    break

            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting vaccination history: {e}")


def _extract_treatments_due(page, medical_data: Dict[str, Any]) -> None:
    """Extract treatments that are currently due."""
    try:
        # Look for treatments due table
        treatments_due_selectors = [
            SELECTORS.treatments_due_table,
            ".treatments-due table",
            ".due-treatments table",
            "[data-treatments-due] table"
        ]

        for table_sel in treatments_due_selectors:
            try:
                rows = extract_table_rows_as_dicts(
                    page,
                    table_sel,
                    [".treatment-name", ".dosage", ".frequency", ".due-date"]
                )

                if rows:
                    for row in rows:
                        treatment = {
                            "name": row.get("Treatment", row.get("Name", "")),
                            "dosage": row.get("Dosage", ""),
                            "frequency": row.get("Frequency", ""),
                            "due_date": normalize_date_string(row.get("Due Date", ""))
                        }
                        if treatment["name"]:
                            medical_data["treatments_due"].append(treatment)
                    break

            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting treatments due: {e}")


def _extract_treatment_history(page, medical_data: Dict[str, Any]) -> None:
    """Extract historical treatment records."""
    try:
        # Look for treatment history table
        treatment_history_selectors = [
            SELECTORS.treatment_history_table,
            ".treatment-history table",
            ".treatment-records table",
            "[data-treatment-history] table"
        ]

        for table_sel in treatment_history_selectors:
            try:
                rows = extract_table_rows_as_dicts(
                    page,
                    table_sel,
                    [".treatment-name", ".dosage", ".frequency", ".start-date", ".end-date", ".notes"]
                )

                if rows:
                    for row in rows:
                        treatment = {
                            "name": row.get("Treatment", row.get("Name", "")),
                            "dosage": row.get("Dosage", ""),
                            "frequency": row.get("Frequency", ""),
                            "start_date": normalize_date_string(row.get("Start Date", "")),
                            "end_date": normalize_date_string(row.get("End Date", "")),
                            "notes": row.get("Notes", "")
                        }
                        if treatment["name"]:
                            medical_data["treatment_history"].append(treatment)
                    break

            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting treatment history: {e}")


def _extract_active_diagnoses(page, medical_data: Dict[str, Any]) -> None:
    """Extract currently active medical diagnoses."""
    try:
        # Look for active diagnoses table
        active_diagnoses_selectors = [
            SELECTORS.active_diagnoses_table,
            ".active-diagnoses table",
            ".current-diagnoses table",
            "[data-active-diagnoses] table"
        ]

        for table_sel in active_diagnoses_selectors:
            try:
                rows = extract_table_rows_as_dicts(
                    page,
                    table_sel,
                    [".condition", ".diagnosed-date", ".notes"]
                )

                if rows:
                    for row in rows:
                        diagnosis = {
                            "condition": row.get("Condition", row.get("Diagnosis", "")),
                            "diagnosed_date": normalize_date_string(row.get("Diagnosed Date", row.get("Date", ""))),
                            "notes": row.get("Notes", "")
                        }
                        if diagnosis["condition"]:
                            medical_data["active_diagnoses"].append(diagnosis)
                    break

            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting active diagnoses: {e}")


def _extract_resolved_diagnoses(page, medical_data: Dict[str, Any]) -> None:
    """Extract previously diagnosed conditions that have been resolved."""
    try:
        # Look for resolved diagnoses table
        resolved_diagnoses_selectors = [
            SELECTORS.resolved_diagnoses_table,
            ".resolved-diagnoses table",
            ".past-diagnoses table",
            "[data-resolved-diagnoses] table"
        ]

        for table_sel in resolved_diagnoses_selectors:
            try:
                rows = extract_table_rows_as_dicts(
                    page,
                    table_sel,
                    [".condition", ".diagnosed-date", ".resolved-date", ".notes"]
                )

                if rows:
                    for row in rows:
                        diagnosis = {
                            "condition": row.get("Condition", row.get("Diagnosis", "")),
                            "diagnosed_date": normalize_date_string(row.get("Diagnosed Date", "")),
                            "resolved_date": normalize_date_string(row.get("Resolved Date", "")),
                            "notes": row.get("Notes", "")
                        }
                        if diagnosis["condition"]:
                            medical_data["resolved_diagnoses"].append(diagnosis)
                    break

            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting resolved diagnoses: {e}")


def _extract_diagnostic_tests(page, medical_data: Dict[str, Any]) -> None:
    """Extract laboratory and diagnostic test results."""
    try:
        # Look for diagnostic tests table
        diagnostic_tests_selectors = [
            SELECTORS.diagnostic_tests_table,
            ".diagnostic-tests table",
            ".lab-tests table",
            "[data-diagnostic-tests] table"
        ]

        for table_sel in diagnostic_tests_selectors:
            try:
                rows = extract_table_rows_as_dicts(
                    page,
                    table_sel,
                    [
                        ".test-type", ".test-name", ".date", ".results",
                        ".results-detail", ".test-by", ".veterinarian", ".notes"
                    ]
                )

                if rows:
                    for row in rows:
                        test = {
                            "test_type": row.get("Test Type", ""),
                            "test_name": row.get("Test Name", row.get("Test", "")),
                            "date": normalize_date_string(row.get("Date", "")),
                            "results": row.get("Results", ""),
                            "results_detail": row.get("Results Detail", ""),
                            "test_by": row.get("Test By", ""),
                            "veterinarian": row.get("Veterinarian", ""),
                            "notes": row.get("Notes", "")
                        }
                        if test["test_name"] or test["results"]:
                            medical_data["diagnostic_tests"].append(test)
                    break

            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting diagnostic tests: {e}")


def _extract_physical_exams(page, medical_data: Dict[str, Any]) -> None:
    """Extract physical examination records."""
    try:
        # Look for physical exams table
        physical_exams_selectors = [
            SELECTORS.physical_exams_table,
            ".physical-exams table",
            ".exam-records table",
            "[data-physical-exams] table"
        ]

        for table_sel in physical_exams_selectors:
            try:
                rows = extract_table_rows_as_dicts(
                    page,
                    table_sel,
                    [".exam-type", ".date-time", ".details"]
                )

                if rows:
                    for row in rows:
                        exam = {
                            "exam_type": row.get("Exam Type", row.get("Type", "")),
                            "date_time": row.get("Date/Time", row.get("Date", "")),
                            "details": row.get("Details", "")
                        }
                        if exam["exam_type"] or exam["details"]:
                            medical_data["physical_exams"].append(exam)
                    break

            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting physical exams: {e}")


def _extract_procedures_surgeries(page, medical_data: Dict[str, Any]) -> None:
    """Extract surgical procedures and medical procedures performed."""
    try:
        # Look for procedures/surgeries table
        procedures_selectors = [
            SELECTORS.procedures_table,
            ".procedures-surgeries table",
            ".surgical-procedures table",
            "[data-procedures] table"
        ]

        for table_sel in procedures_selectors:
            try:
                rows = extract_table_rows_as_dicts(
                    page,
                    table_sel,
                    [".procedure-type", ".date-time", ".details"]
                )

                if rows:
                    for row in rows:
                        procedure = {
                            "procedure_type": row.get("Procedure Type", row.get("Type", "")),
                            "date_time": row.get("Date/Time", row.get("Date", "")),
                            "details": row.get("Details", "")
                        }
                        if procedure["procedure_type"] or procedure["details"]:
                            medical_data["procedures_surgeries"].append(procedure)
                    break

            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting procedures/surgeries: {e}")
