"""
Detailed medical parsing functions for ShelterLuv scraper.

Handles extraction of comprehensive medical data including vaccinations, treatments,
diagnoses, tests, exams, and procedures from the Complete Medical History page.
"""

from typing import Any, Dict


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

        # 1. Microchip Number / Issuer / Issued Date
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

        # 2. Previous Shelter ID
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

        # 3. Weight History
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

        # 4. Vaccination History
        _extract_vaccination_history_detailed(page, medical_data)

        # 5. Treatments Next Due
        _extract_treatments_due(page, medical_data)

        # 6. Treatment History
        _extract_treatment_history(page, medical_data)

        # 7. Active Diagnoses
        _extract_active_diagnoses(page, medical_data)

        # 8. Resolved Diagnoses
        _extract_resolved_diagnoses(page, medical_data)

        # 9. Diagnostic Tests History
        _extract_diagnostic_tests(page, medical_data)

        # 10. Physical Exam History
        _extract_physical_exams(page, medical_data)

        # 11. Procedures/Surgeries History
        _extract_procedures_surgeries(page, medical_data)

        # Store the comprehensive medical data (ensure it's always present)
        if not medical_data["vaccinations"] and not medical_data["treatments_due"] and not medical_data["treatment_history"] and not medical_data["active_diagnoses"] and not medical_data["resolved_diagnoses"] and not medical_data["diagnostic_tests"] and not medical_data["physical_exams"] and not medical_data["procedures_surgeries"]:
            # If no medical data was found, don't set MedicalHistory to keep it optional
            pass
        else:
            result["MedicalHistory"] = medical_data

    except Exception as e:
        print(f"Error extracting medical history: {e}")


def _extract_vaccination_history_detailed(page, medical_data: Dict[str, Any]) -> None:
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

        vaccination_table = None
        for xpath in possible_xpaths:
            table = page.locator(f"xpath={xpath}")
            if table.count() > 0:
                vaccination_table = table
                break

        if vaccination_table:
            rows = vaccination_table.locator("tbody tr")
            row_count = rows.count()

            for i in range(row_count):
                try:
                    row = rows.nth(i)
                    cells = row.locator("td")
                    cell_count = cells.count()

                    if cell_count >= 4:
                        vaccination = {
                            "vaccine": cells.nth(0).inner_text(timeout=1000).strip(),
                            "date_given": cells.nth(1).inner_text(timeout=1000).strip(),
                            "expires": cells.nth(2).inner_text(timeout=1000).strip(),
                            "notes": cells.nth(3).inner_text(timeout=1000).strip() if cell_count > 3 else ""
                        }

                        if vaccination["vaccine"]:  # Only add if vaccine name exists
                            medical_data["vaccinations"].append(vaccination)

                except Exception as e:
                    print(f"Error extracting vaccination row {i}: {e}")
                    continue

    except Exception as e:
        print(f"Error extracting vaccination history: {e}")


def _extract_treatments_due(page, medical_data: Dict[str, Any]) -> None:
    """Extract treatments next due."""
    try:
        # Find the "Treatments Next Due" table
        possible_xpaths = [
            "//h2[normalize-space()='Treatments Next Due']/following-sibling::table[1]",
            "//h2[normalize-space()='Treatments Next Due']/following::table[1]",
            "//h2[contains(text(),'Treatments Next Due')]/following-sibling::table[1]",
            "//table[preceding::h2[contains(text(),'Treatments Next Due')]][1]"
        ]

        treatments_table = None
        for xpath in possible_xpaths:
            table = page.locator(f"xpath={xpath}")
            if table.count() > 0:
                treatments_table = table
                break

        if treatments_table:
            rows = treatments_table.locator("tbody tr")
            row_count = rows.count()

            for i in range(row_count):
                try:
                    row = rows.nth(i)
                    cells = row.locator("td")
                    cell_count = cells.count()

                    if cell_count >= 3:
                        treatment = {
                            "treatment": cells.nth(0).inner_text(timeout=1000).strip(),
                            "next_due": cells.nth(1).inner_text(timeout=1000).strip(),
                            "frequency": cells.nth(2).inner_text(timeout=1000).strip() if cell_count > 2 else ""
                        }

                        if treatment["treatment"]:  # Only add if treatment name exists
                            medical_data["treatments_due"].append(treatment)

                except Exception as e:
                    print(f"Error extracting treatment due row {i}: {e}")
                    continue

    except Exception as e:
        print(f"Error extracting treatments due: {e}")


def _extract_treatment_history(page, medical_data: Dict[str, Any]) -> None:
    """Extract treatment history."""
    try:
        # Find the "Treatment History" table
        possible_xpaths = [
            "//h2[normalize-space()='Treatment History']/following-sibling::table[1]",
            "//h2[normalize-space()='Treatment History']/following::table[1]",
            "//h2[contains(text(),'Treatment History')]/following-sibling::table[1]",
            "//table[preceding::h2[contains(text(),'Treatment History')]][1]"
        ]

        treatments_table = None
        for xpath in possible_xpaths:
            table = page.locator(f"xpath={xpath}")
            if table.count() > 0:
                treatments_table = table
                break

        if treatments_table:
            rows = treatments_table.locator("tbody tr")
            row_count = rows.count()

            for i in range(row_count):
                try:
                    row = rows.nth(i)
                    cells = row.locator("td")
                    cell_count = cells.count()

                    if cell_count >= 4:
                        treatment = {
                            "treatment": cells.nth(0).inner_text(timeout=1000).strip(),
                            "date_given": cells.nth(1).inner_text(timeout=1000).strip(),
                            "given_by": cells.nth(2).inner_text(timeout=1000).strip(),
                            "notes": cells.nth(3).inner_text(timeout=1000).strip() if cell_count > 3 else ""
                        }

                        if treatment["treatment"]:  # Only add if treatment name exists
                            medical_data["treatment_history"].append(treatment)

                except Exception as e:
                    print(f"Error extracting treatment history row {i}: {e}")
                    continue

    except Exception as e:
        print(f"Error extracting treatment history: {e}")


def _extract_active_diagnoses(page, medical_data: Dict[str, Any]) -> None:
    """Extract active diagnoses."""
    try:
        # Find the "Active Diagnoses" table
        possible_xpaths = [
            "//h2[normalize-space()='Active Diagnoses']/following-sibling::table[1]",
            "//h2[normalize-space()='Active Diagnoses']/following::table[1]",
            "//h2[contains(text(),'Active Diagnoses')]/following-sibling::table[1]",
            "//table[preceding::h2[contains(text(),'Active Diagnoses')]][1]"
        ]

        diagnoses_table = None
        for xpath in possible_xpaths:
            table = page.locator(f"xpath={xpath}")
            if table.count() > 0:
                diagnoses_table = table
                break

        if diagnoses_table:
            rows = diagnoses_table.locator("tbody tr")
            row_count = rows.count()

            for i in range(row_count):
                try:
                    row = rows.nth(i)
                    cells = row.locator("td")
                    cell_count = cells.count()

                    if cell_count >= 3:
                        diagnosis = {
                            "diagnosis": cells.nth(0).inner_text(timeout=1000).strip(),
                            "date_diagnosed": cells.nth(1).inner_text(timeout=1000).strip(),
                            "diagnosed_by": cells.nth(2).inner_text(timeout=1000).strip(),
                            "notes": cells.nth(3).inner_text(timeout=1000).strip() if cell_count > 3 else ""
                        }

                        if diagnosis["diagnosis"]:  # Only add if diagnosis name exists
                            medical_data["active_diagnoses"].append(diagnosis)

                except Exception as e:
                    print(f"Error extracting active diagnosis row {i}: {e}")
                    continue

    except Exception as e:
        print(f"Error extracting active diagnoses: {e}")


def _extract_resolved_diagnoses(page, medical_data: Dict[str, Any]) -> None:
    """Extract resolved diagnoses."""
    try:
        # Find the "Resolved Diagnoses" table
        possible_xpaths = [
            "//h2[normalize-space()='Resolved Diagnoses']/following-sibling::table[1]",
            "//h2[normalize-space()='Resolved Diagnoses']/following::table[1]",
            "//h2[contains(text(),'Resolved Diagnoses')]/following-sibling::table[1]",
            "//table[preceding::h2[contains(text(),'Resolved Diagnoses')]][1]"
        ]

        diagnoses_table = None
        for xpath in possible_xpaths:
            table = page.locator(f"xpath={xpath}")
            if table.count() > 0:
                diagnoses_table = table
                break

        if diagnoses_table:
            rows = diagnoses_table.locator("tbody tr")
            row_count = rows.count()

            for i in range(row_count):
                try:
                    row = rows.nth(i)
                    cells = row.locator("td")
                    cell_count = cells.count()

                    if cell_count >= 4:
                        diagnosis = {
                            "diagnosis": cells.nth(0).inner_text(timeout=1000).strip(),
                            "date_resolved": cells.nth(1).inner_text(timeout=1000).strip(),
                            "resolved_by": cells.nth(2).inner_text(timeout=1000).strip(),
                            "notes": cells.nth(3).inner_text(timeout=1000).strip() if cell_count > 3 else ""
                        }

                        if diagnosis["diagnosis"]:  # Only add if diagnosis name exists
                            medical_data["resolved_diagnoses"].append(diagnosis)

                except Exception as e:
                    print(f"Error extracting resolved diagnosis row {i}: {e}")
                    continue

    except Exception as e:
        print(f"Error extracting resolved diagnoses: {e}")


def _extract_diagnostic_tests(page, medical_data: Dict[str, Any]) -> None:
    """Extract diagnostic tests history."""
    try:
        # Find the "Diagnostic Tests History" table
        possible_xpaths = [
            "//h2[normalize-space()='Diagnostic Tests History']/following-sibling::table[1]",
            "//h2[normalize-space()='Diagnostic Tests History']/following::table[1]",
            "//h2[contains(text(),'Diagnostic Tests')]/following-sibling::table[1]",
            "//table[preceding::h2[contains(text(),'Diagnostic Tests')]][1]"
        ]

        tests_table = None
        for xpath in possible_xpaths:
            table = page.locator(f"xpath={xpath}")
            if table.count() > 0:
                tests_table = table
                break

        if tests_table:
            rows = tests_table.locator("tbody tr")
            row_count = rows.count()

            for i in range(row_count):
                try:
                    row = rows.nth(i)
                    cells = row.locator("td")
                    cell_count = cells.count()

                    if cell_count >= 4:
                        test = {
                            "test": cells.nth(0).inner_text(timeout=1000).strip(),
                            "date_performed": cells.nth(1).inner_text(timeout=1000).strip(),
                            "result": cells.nth(2).inner_text(timeout=1000).strip(),
                            "performed_by": cells.nth(3).inner_text(timeout=1000).strip() if cell_count > 3 else ""
                        }

                        if test["test"]:  # Only add if test name exists
                            medical_data["diagnostic_tests"].append(test)

                except Exception as e:
                    print(f"Error extracting diagnostic test row {i}: {e}")
                    continue

    except Exception as e:
        print(f"Error extracting diagnostic tests: {e}")


def _extract_physical_exams(page, medical_data: Dict[str, Any]) -> None:
    """Extract physical exam history."""
    try:
        # Find the "Physical Exam History" table
        possible_xpaths = [
            "//h2[normalize-space()='Physical Exam History']/following-sibling::table[1]",
            "//h2[normalize-space()='Physical Exam History']/following::table[1]",
            "//h2[contains(text(),'Physical Exam')]/following-sibling::table[1]",
            "//table[preceding::h2[contains(text(),'Physical Exam')]][1]"
        ]

        exams_table = None
        for xpath in possible_xpaths:
            table = page.locator(f"xpath={xpath}")
            if table.count() > 0:
                exams_table = table
                break

        if exams_table:
            rows = exams_table.locator("tbody tr")
            row_count = rows.count()

            for i in range(row_count):
                try:
                    row = rows.nth(i)
                    cells = row.locator("td")
                    cell_count = cells.count()

                    if cell_count >= 4:
                        exam = {
                            "exam_type": cells.nth(0).inner_text(timeout=1000).strip(),
                            "date_performed": cells.nth(1).inner_text(timeout=1000).strip(),
                            "performed_by": cells.nth(2).inner_text(timeout=1000).strip(),
                            "notes": cells.nth(3).inner_text(timeout=1000).strip() if cell_count > 3 else ""
                        }

                        if exam["exam_type"]:  # Only add if exam type exists
                            medical_data["physical_exams"].append(exam)

                except Exception as e:
                    print(f"Error extracting physical exam row {i}: {e}")
                    continue

    except Exception as e:
        print(f"Error extracting physical exams: {e}")


def _extract_procedures_surgeries(page, medical_data: Dict[str, Any]) -> None:
    """Extract procedures/surgeries history."""
    try:
        # Find the "Procedures/Surgeries History" table
        possible_xpaths = [
            "//h2[normalize-space()='Procedures/Surgeries History']/following-sibling::table[1]",
            "//h2[normalize-space()='Procedures/Surgeries History']/following::table[1]",
            "//h2[contains(text(),'Procedures')]/following-sibling::table[1]",
            "//h2[contains(text(),'Surgeries')]/following-sibling::table[1]",
            "//table[preceding::h2[contains(text(),'Procedure') or contains(text(),'Surgery')]][1]"
        ]

        procedures_table = None
        for xpath in possible_xpaths:
            table = page.locator(f"xpath={xpath}")
            if table.count() > 0:
                procedures_table = table
                break

        if procedures_table:
            rows = procedures_table.locator("tbody tr")
            row_count = rows.count()

            for i in range(row_count):
                try:
                    row = rows.nth(i)
                    cells = row.locator("td")
                    cell_count = cells.count()

                    if cell_count >= 4:
                        procedure = {
                            "procedure": cells.nth(0).inner_text(timeout=1000).strip(),
                            "date_performed": cells.nth(1).inner_text(timeout=1000).strip(),
                            "performed_by": cells.nth(2).inner_text(timeout=1000).strip(),
                            "notes": cells.nth(3).inner_text(timeout=1000).strip() if cell_count > 3 else ""
                        }

                        if procedure["procedure"]:  # Only add if procedure name exists
                            medical_data["procedures_surgeries"].append(procedure)

                except Exception as e:
                    print(f"Error extracting procedure/surgery row {i}: {e}")
                    continue

    except Exception as e:
        print(f"Error extracting procedures/surgeries: {e}")


def _extract_vaccination_history(page, result: Dict[str, Any]) -> None:
    """Extract vaccination history for simpler extraction (not detailed)."""
    try:
        # This is a simpler version for basic extraction
        vaccination_selectors = [
            "table:has-text('Vaccination')",
            "[data-section='vaccinations'] table",
            "text=/Vaccination/",
        ]

        for selector in vaccination_selectors:
            try:
                table = page.locator(selector).first
                if table.count() > 0:
                    rows = table.locator("tbody tr")
                    vaccinations = []

                    for i in range(min(rows.count(), 10)):  # Limit to reasonable number
                        try:
                            row = rows.nth(i)
                            cells = row.locator("td")
                            if cells.count() >= 2:
                                vaccine_name = cells.nth(0).inner_text(timeout=1000).strip()
                                vaccine_date = cells.nth(1).inner_text(timeout=1000).strip()
                                if vaccine_name:
                                    vaccinations.append(f"{vaccine_name} ({vaccine_date})")
                        except Exception:
                            continue

                    if vaccinations:
                        result["VaccinationHistory"] = vaccinations
                        break

            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting vaccination history: {e}")
