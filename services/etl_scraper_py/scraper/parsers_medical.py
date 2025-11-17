"""
Medical field parsing functions for ShelterLuv scraper.
Handles medical tabs, diagnoses, treatments, vaccinations, etc.
Prefers structured data, falls back to HTML parsing.
"""

from typing import Any, Dict, List

from .navigation import SELECTORS


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


def _extract_age_panel(page, result: Dict[str, Any]) -> None:
    """Extract age-related information from the age panel."""
    try:
        # Look for age information in various formats
        age_selectors = [
            ".age-display",
            "[data-age]",
            ".animal-age"
        ]

        for selector in age_selectors:
            try:
                age_elem = page.locator(selector)
                if age_elem.count() > 0:
                    age_text = age_elem.first.inner_text(timeout=1000).strip()
                    if age_text:
                        # Try to extract numeric age
                        import re
                        age_match = re.search(r'(\d+(?:\.\d+)?)\s*years?', age_text, re.IGNORECASE)
                        if age_match:
                            result["AgeYears"] = float(age_match.group(1))

                            # Generate display string
                            years = int(float(age_match.group(1)))
                            months = int((float(age_match.group(1)) - years) * 12)
                            if months == 0:
                                result["AgeDisplay"] = f"{years} year{'s' if years != 1 else ''}"
                            else:
                                result["AgeDisplay"] = f"{years} year{'s' if years != 1 else ''} {months} month{'s' if months != 1 else ''}"
                        else:
                            result["AgeDisplay"] = age_text
                        break
            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting age panel: {e}")


def parse_medical_from_raw_record(raw_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract medical information from a canonical raw animal record.

    Args:
        raw_record: Canonical raw animal record with structured medical data.

    Returns:
        Dict with medical fields like MedicalSummary, MedicalDiagnoses, etc.
    """
    # For now, this is a placeholder - medical data often comes from tab scraping
    # rather than being part of the initial record structure
    return {}


def scrape_medical_fields(navigation) -> Dict[str, str]:
    """Scrape medical tab data."""
    result: Dict[str, str] = {}
    medical_tab = SELECTORS["tabs"]["medical"]  # type: ignore
    if not navigation._click_tab(medical_tab, timeout_ms=2000):
        return result

    subtabs = SELECTORS["subtabs"]["medical"]  # type: ignore
    result["MedicalSummary"] = navigation._extract_tab_text(subtabs["summary"])  # type: ignore
    result["MedicalDiagnoses"] = navigation._extract_tab_text(subtabs["diagnoses"])  # type: ignore
    result["MedicalDiagnosticTests"] = navigation._extract_tab_text(subtabs["diagnostic_tests"])  # type: ignore
    result["MedicalVaccines"] = navigation._extract_tab_text(subtabs["vaccines"])  # type: ignore
    result["MedicalDailyObservations"] = navigation._extract_tab_text(subtabs["daily_observations"])  # type: ignore
    result["MedicalPhysicalExams"] = navigation._extract_tab_text(subtabs["physical_exams"])  # type: ignore
    result["MedicalTreatments"] = navigation._extract_tab_text(subtabs["treatments"])  # type: ignore
    result["MedicalProcedures"] = navigation._extract_tab_text(subtabs["procedures"])  # type: ignore
    return result


def scrape_medical_history_from_comprehensive_page(page) -> Dict[str, Any]:
    """
    Extract complete medical history from the comprehensive medical history page.
    This is a comprehensive extraction that includes all medical data sections.
    """
    result = {
        "vaccinations": [],
        "treatments_due": [],
        "treatment_history": [],
        "active_diagnoses": [],
        "resolved_diagnoses": [],
        "diagnostic_tests": [],
        "physical_exams": [],
        "procedures_surgeries": []
    }

    try:
        # 1. Microchip Number / Issuer / Implant Date
        _extract_microchip_info(page, result)

        # 2. Previous Shelter ID
        _extract_previous_shelter_info(page, result)

        # 3. Weight History
        _extract_weight_info(page, result)

        # 4. Vaccination History
        _extract_vaccination_history(page, result)

        # 5. Treatments Next Due
        _extract_treatments_due(page, result)

        # 6. Treatment History
        _extract_treatment_history(page, result)

        # 7. Active Diagnoses
        _extract_active_diagnoses(page, result)

        # 8. Resolved Diagnoses
        _extract_resolved_diagnoses(page, result)

        # 9. Diagnostic Tests History
        _extract_diagnostic_tests(page, result)

        # 10. Physical Exam History
        _extract_physical_exams(page, result)

        # 11. Procedures/Surgeries History
        _extract_procedures_surgeries(page, result)

    except Exception as e:
        print(f"Error extracting medical history: {e}")

    return result


def _extract_microchip_info(page, result: Dict[str, Any]) -> None:
    """Extract microchip information from ID Numbers table."""
    try:
        microchip_table_xpath = "//h1[normalize-space()='Complete Medical History']/following::h2[normalize-space()='ID Numbers']/following::table[1]"
        microchip_table = page.locator(f"xpath={microchip_table_xpath}")
        if microchip_table.count() > 0:
            rows = microchip_table.locator("tbody tr")
            if rows.count() > 0:
                first_row = rows.first
                cells = first_row.locator("td")
                if cells.count() >= 3:
                    result["MicrochipNumber"] = cells.nth(0).inner_text(timeout=1000).strip()
                    result["MicrochipImplantDate"] = cells.nth(1).inner_text(timeout=1000).strip()
                    result["MicrochipIssuer"] = cells.nth(2).inner_text(timeout=1000).strip()
    except Exception as e:
        print(f"Error extracting microchip info: {e}")


def _extract_previous_shelter_info(page, result: Dict[str, Any]) -> None:
    """Extract previous shelter information from ID Numbers table."""
    try:
        prev_shelter_table_xpath = "//h1[normalize-space()='Complete Medical History']/following::h2[normalize-space()='ID Numbers']/following::table[2]"
        prev_table = page.locator(f"xpath={prev_shelter_table_xpath}")
        if prev_table.count() > 0:
            rows = prev_table.locator("tbody tr")
            if rows.count() > 0:
                first_row = rows.first
                cells = first_row.locator("td")
                if cells.count() >= 3:
                    result["PreviousShelterId"] = cells.nth(0).inner_text(timeout=1000).strip()
                    result["PreviousShelterType"] = cells.nth(1).inner_text(timeout=1000).strip()
                    result["PreviousShelterIssuer"] = cells.nth(2).inner_text(timeout=1000).strip()
    except Exception as e:
        print(f"Error extracting previous shelter info: {e}")


def _extract_weight_info(page, result: Dict[str, Any]) -> None:
    """Extract current weight from Weight table."""
    try:
        weight_table_xpath = "//h1[normalize-space()='Complete Medical History']/following::h2[normalize-space()='Weight']/following::table[1]"
        weight_table = page.locator(f"xpath={weight_table_xpath}")
        if weight_table.count() > 0:
            rows = weight_table.locator("tbody tr")
            if rows.count() > 0:
                first_row = rows.first
                cells = first_row.locator("td")
                if cells.count() >= 2:
                    weight_value = cells.nth(0).inner_text(timeout=1000).strip()
                    if weight_value:
                        result["Weight"] = weight_value
    except Exception as e:
        print(f"Error extracting weight info: {e}")


def _extract_vaccination_history(page, result: Dict[str, Any]) -> None:
    """Extract detailed vaccination history."""
    try:
        # Try multiple XPath selectors to find the vaccination table
        possible_xpaths = [
            "//h2[normalize-space()='Vaccination History']/following-sibling::table[1]",
            "//h2[normalize-space()='Vaccination History']/following::table[1]",
            "//h2[contains(text(),'Vaccination')]/following-sibling::table[1]",
            "//h2[contains(text(),'Vaccination')]/following::table[1]",
            "//table[preceding::h2[contains(text(),'Vaccination')]][1]"
        ]

        vaccine_table = None
        for xpath in possible_xpaths:
            table = page.locator(f"xpath={xpath}")
            if table.count() > 0:
                vaccine_table = table
                break

        if vaccine_table is None:
            return

        rows = vaccine_table.locator("tbody tr")
        vaccinations = []

        for i in range(rows.count()):
            try:
                row = rows.nth(i)
                cells = row.locator("td")
                cell_count = cells.count()

                if cell_count >= 3:
                    vaccine_info = {
                        "name": cells.nth(0).inner_text(timeout=1000).strip(),
                        "date": cells.nth(1).inner_text(timeout=1000).strip(),
                        "status": cells.nth(2).inner_text(timeout=1000).strip()
                    }

                    # Add additional fields if available
                    if cell_count >= 4:
                        vaccine_info["lot_number"] = cells.nth(3).inner_text(timeout=1000).strip()
                    if cell_count >= 5:
                        vaccine_info["expiration_date"] = cells.nth(4).inner_text(timeout=1000).strip()
                    if cell_count >= 6:
                        vaccine_info["source"] = cells.nth(5).inner_text(timeout=1000).strip()
                    if cell_count >= 7:
                        vaccine_info["route"] = cells.nth(6).inner_text(timeout=1000).strip()
                    if cell_count >= 8:
                        vaccine_info["site"] = cells.nth(7).inner_text(timeout=1000).strip()
                    if cell_count >= 9:
                        vaccine_info["vaccinated_by"] = cells.nth(8).inner_text(timeout=1000).strip()

                    # Check for rabies tag number
                    if "rabies" in vaccine_info.get("name", "").lower():
                        if cell_count >= 10:
                            rabies_tag = cells.nth(9).inner_text(timeout=1000).strip()
                            if rabies_tag and rabies_tag != "None":
                                result["RabiesTagNumber"] = rabies_tag

                    vaccinations.append(vaccine_info)

            except Exception as e:
                print(f"Error processing vaccination row {i}: {e}")
                continue

        result["vaccinations"] = vaccinations

    except Exception as e:
        print(f"Error extracting vaccination history: {e}")


def _extract_treatments_due(page, result: Dict[str, Any]) -> None:
    """Extract treatments next due."""
    try:
        treatments_table_xpath = "//h2[normalize-space()='Treatments Next Due']/following::table[1]"
        treatments_table = page.locator(f"xpath={treatments_table_xpath}")
        if treatments_table.count() > 0:
            rows = treatments_table.locator("tbody tr")
            treatments_due = []
            for i in range(rows.count()):
                try:
                    row = rows.nth(i)
                    cells = row.locator("td")
                    if cells.count() >= 4:
                        treatment_info = {
                            "name": cells.nth(0).inner_text(timeout=1000).strip(),
                            "dosage": cells.nth(1).inner_text(timeout=1000).strip(),
                            "frequency": cells.nth(2).inner_text(timeout=1000).strip(),
                            "due_date": cells.nth(3).inner_text(timeout=1000).strip()
                        }
                        # Add status if available
                        if cells.count() >= 5:
                            treatment_info["status"] = cells.nth(4).inner_text(timeout=1000).strip()
                        treatments_due.append(treatment_info)
                except Exception:
                    continue
            result["treatments_due"] = treatments_due
    except Exception as e:
        print(f"Error extracting treatments due: {e}")


def _extract_treatment_history(page, result: Dict[str, Any]) -> None:
    """Extract treatment history."""
    try:
        treatments_table_xpath = "//h2[normalize-space()='Treatment History']/following::table[1]"
        treatments_table = page.locator(f"xpath={treatments_table_xpath}")
        if treatments_table.count() > 0:
            rows = treatments_table.locator("tbody tr")
            treatment_history = []
            for i in range(rows.count()):
                try:
                    row = rows.nth(i)
                    cells = row.locator("td")
                    if cells.count() >= 6:
                        treatment_info = {
                            "name": cells.nth(0).inner_text(timeout=1000).strip(),
                            "dosage": cells.nth(1).inner_text(timeout=1000).strip(),
                            "frequency": cells.nth(2).inner_text(timeout=1000).strip(),
                            "start_date": cells.nth(3).inner_text(timeout=1000).strip(),
                            "end_date": cells.nth(4).inner_text(timeout=1000).strip(),
                            "notes": cells.nth(5).inner_text(timeout=1000).strip()
                        }
                        # Add veterinarian if available
                        if cells.count() >= 7:
                            treatment_info["veterinarian"] = cells.nth(6).inner_text(timeout=1000).strip()
                        treatment_history.append(treatment_info)
                except Exception:
                    continue
            result["treatment_history"] = treatment_history
    except Exception as e:
        print(f"Error extracting treatment history: {e}")


def _extract_active_diagnoses(page, result: Dict[str, Any]) -> None:
    """Extract active diagnoses."""
    try:
        diagnoses_table_xpath = "//h2[normalize-space()='Active Diagnoses']/following::table[1]"
        diagnoses_table = page.locator(f"xpath={diagnoses_table_xpath}")
        if diagnoses_table.count() > 0:
            rows = diagnoses_table.locator("tbody tr")
            active_diagnoses = []
            for i in range(rows.count()):
                try:
                    row = rows.nth(i)
                    cells = row.locator("td")
                    if cells.count() >= 3:
                        diagnosis_info = {
                            "condition": cells.nth(0).inner_text(timeout=1000).strip(),
                            "diagnosed_date": cells.nth(1).inner_text(timeout=1000).strip(),
                            "notes": cells.nth(2).inner_text(timeout=1000).strip()
                        }
                        active_diagnoses.append(diagnosis_info)
                except Exception:
                    continue
            result["active_diagnoses"] = active_diagnoses
    except Exception as e:
        print(f"Error extracting active diagnoses: {e}")


def _extract_resolved_diagnoses(page, result: Dict[str, Any]) -> None:
    """Extract resolved diagnoses."""
    try:
        diagnoses_table_xpath = "//h2[normalize-space()='Resolved Diagnoses']/following::table[1]"
        diagnoses_table = page.locator(f"xpath={diagnoses_table_xpath}")
        if diagnoses_table.count() > 0:
            rows = diagnoses_table.locator("tbody tr")
            resolved_diagnoses = []
            for i in range(rows.count()):
                try:
                    row = rows.nth(i)
                    cells = row.locator("td")
                    if cells.count() >= 4:
                        diagnosis_info = {
                            "condition": cells.nth(0).inner_text(timeout=1000).strip(),
                            "diagnosed_date": cells.nth(1).inner_text(timeout=1000).strip(),
                            "resolved_date": cells.nth(2).inner_text(timeout=1000).strip(),
                            "notes": cells.nth(3).inner_text(timeout=1000).strip()
                        }
                        resolved_diagnoses.append(diagnosis_info)
                except Exception:
                    continue
            result["resolved_diagnoses"] = resolved_diagnoses
    except Exception as e:
        print(f"Error extracting resolved diagnoses: {e}")


def _extract_diagnostic_tests(page, result: Dict[str, Any]) -> None:
    """Extract diagnostic tests history."""
    try:
        tests_table_xpath = "//h2[normalize-space()='Diagnostic Tests History']/following::table[1]"
        tests_table = page.locator(f"xpath={tests_table_xpath}")
        if tests_table.count() > 0:
            rows = tests_table.locator("tbody tr")
            diagnostic_tests = []
            for i in range(rows.count()):
                try:
                    row = rows.nth(i)
                    cells = row.locator("td")
                    if cells.count() >= 6:
                        test_info = {
                            "test_type": cells.nth(0).inner_text(timeout=1000).strip(),
                            "test_name": cells.nth(1).inner_text(timeout=1000).strip(),
                            "date": cells.nth(2).inner_text(timeout=1000).strip(),
                            "results": cells.nth(3).inner_text(timeout=1000).strip(),
                            "results_detail": cells.nth(4).inner_text(timeout=1000).strip(),
                            "test_by": cells.nth(5).inner_text(timeout=1000).strip()
                        }
                        # Add veterinarian and notes if available
                        if cells.count() >= 7:
                            test_info["veterinarian"] = cells.nth(6).inner_text(timeout=1000).strip()
                        if cells.count() >= 8:
                            test_info["notes"] = cells.nth(7).inner_text(timeout=1000).strip()
                        diagnostic_tests.append(test_info)
                except Exception:
                    continue
            result["diagnostic_tests"] = diagnostic_tests
    except Exception as e:
        print(f"Error extracting diagnostic tests: {e}")


def _extract_physical_exams(page, result: Dict[str, Any]) -> None:
    """Extract physical exam history."""
    try:
        exam_cards_xpath = "//h2[normalize-space()='Physical Exam History']/following::div[contains(@class,'text-xs leading-4 border-l-8')]"
        exam_cards = page.locator(f"xpath={exam_cards_xpath}")

        physical_exams = []
        for i in range(exam_cards.count()):
            try:
                card = exam_cards.nth(i)
                exam_info = {}

                # Exam type from header
                header_xpath = ".//div[@class='flex justify-between items-start']/div[1]"
                header_elem = card.locator(f"xpath={header_xpath}")
                if header_elem.count() > 0:
                    exam_info["exam_type"] = header_elem.first.inner_text(timeout=1000).strip()

                # Date and time
                datetime_xpath = ".//div[@class='flex justify-between items-start']/div[2]"
                datetime_elem = card.locator(f"xpath={datetime_xpath}")
                if datetime_elem.count() > 0:
                    exam_info["date_time"] = datetime_elem.first.inner_text(timeout=1000).strip()

                # Exam details
                details_xpath = ".//div[contains(@class,'mt-2')]"
                details_elem = card.locator(f"xpath={details_xpath}")
                if details_elem.count() > 0:
                    exam_info["details"] = details_elem.first.inner_text(timeout=1000).strip()

                if exam_info:
                    physical_exams.append(exam_info)

            except Exception:
                continue

        result["physical_exams"] = physical_exams
    except Exception as e:
        print(f"Error extracting physical exams: {e}")


def _extract_procedures_surgeries(page, result: Dict[str, Any]) -> None:
    """Extract procedures and surgeries history."""
    try:
        procedure_cards_xpath = "//h2[normalize-space()='Procedures/Surgeries History']/following::div[contains(@class,'text-xs leading-4 border-l-8')]"
        procedure_cards = page.locator(f"xpath={procedure_cards_xpath}")

        procedures_surgeries = []
        for i in range(procedure_cards.count()):
            try:
                card = procedure_cards.nth(i)
                procedure_info = {}

                # Procedure type from header
                header_xpath = ".//div[@class='flex justify-between items-start']/div[1]"
                header_elem = card.locator(f"xpath={header_xpath}")
                if header_elem.count() > 0:
                    procedure_info["procedure_type"] = header_elem.first.inner_text(timeout=1000).strip()

                # Date and time
                datetime_xpath = ".//div[@class='flex justify-between items-start']/div[2]"
                datetime_elem = card.locator(f"xpath={datetime_xpath}")
                if datetime_elem.count() > 0:
                    procedure_info["date_time"] = datetime_elem.first.inner_text(timeout=1000).strip()

                # Procedure details
                details_xpath = ".//div[contains(@class,'mt-2')]"
                details_elem = card.locator(f"xpath={details_xpath}")
                if details_elem.count() > 0:
                    procedure_info["details"] = details_elem.first.inner_text(timeout=1000).strip()

                if procedure_info:
                    procedures_surgeries.append(procedure_info)

            except Exception:
                continue

        result["procedures_surgeries"] = procedures_surgeries
    except Exception as e:
        print(f"Error extracting procedures/surgeries: {e}")
