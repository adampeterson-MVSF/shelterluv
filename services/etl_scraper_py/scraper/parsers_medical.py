"""
Medical history parsing functions for ShelterLuv scraper.

Handles extraction of comprehensive medical data including:
- Microchip information
- Vaccination history
- Treatment history
- Diagnoses
- Diagnostic tests
- Physical exams
- Procedures
- Medical memos
"""

from typing import Any, Dict, List


def scrape_medical_fields(navigation) -> Dict[str, Any]:
    """Scrape medical fields using navigation - wrapper for extract_medical_history."""
    # Get the page from navigation
    page = navigation.page if hasattr(navigation, 'page') else navigation

    # Call the main extraction function
    return extract_medical_history(page)


def extract_medical_history(page) -> Dict[str, Any]:
    """Extract complete medical history from ShelterLuv summary page."""
    medical_data = {
        "MicrochipInfo": {},
        "RabiesTag": {},
        "VaccinationHistory": [],
        "TreatmentsDue": [],
        "TreatmentHistory": [],
        "Diagnoses": [],
        "DiagnosticTests": [],
        "PhysicalExams": [],
        "Procedures": [],
        "MedicalMemos": []
    }

    try:
        # Find the Complete Medical History section
        medical_header = page.locator("h1:has-text('Complete Medical History')")
        if medical_header.count() == 0:
            return medical_data

        # Extract microchip information
        medical_data["MicrochipInfo"] = extract_microchip_info(page)

        # Extract rabies tag information
        medical_data["RabiesTag"] = extract_rabies_tag(page)

        # Extract vaccination history
        medical_data["VaccinationHistory"] = extract_vaccination_history(page)

        # Extract treatments due
        medical_data["TreatmentsDue"] = extract_treatments_due(page)

        # Extract treatment history
        medical_data["TreatmentHistory"] = extract_treatment_history(page)

        # Extract diagnoses
        medical_data["Diagnoses"] = extract_diagnoses(page)

        # Extract diagnostic tests
        medical_data["DiagnosticTests"] = extract_diagnostic_tests(page)

        # Extract physical exams
        medical_data["PhysicalExams"] = extract_physical_exams(page)

        # Extract procedures
        medical_data["Procedures"] = extract_procedures(page)

        # Extract medical memos
        medical_data["MedicalMemos"] = extract_medical_memos(page)

    except Exception as e:
        print(f"Error extracting medical history: {e}")

    return medical_data


def extract_microchip_info(page) -> Dict[str, Any]:
    """Extract microchip information."""
    microchip_info = {}

    try:
        # Find ID Numbers section
        id_section = page.locator("h2:has-text('ID Numbers')")
        if id_section.count() == 0:
            return microchip_info

        # Look for microchip table
        microchip_table = page.locator("h2:has-text('ID Numbers') ~ div table")
        if microchip_table.count() == 0:
            return microchip_info

        # Extract table data - HTML has data directly in td elements, not labels
        rows = microchip_table.locator("tbody tr")
        for i in range(rows.count()):
            row = rows.nth(i)
            cells = row.locator("td")

            if cells.count() >= 3:
                # Based on HTML structure: number, issued_date, issuer
                number = cells.nth(0).inner_text(timeout=1000).strip()
                issued_date = cells.nth(1).inner_text(timeout=1000).strip()
                issuer = cells.nth(2).inner_text(timeout=1000).strip() if cells.count() > 2 else ""

                if number and number != "N/A":
                    microchip_info["number"] = number
                    microchip_info["issued_date"] = issued_date
                    microchip_info["issuer"] = issuer

    except Exception as e:
        print(f"Error extracting microchip info: {e}")

    return microchip_info


def extract_rabies_tag(page) -> Dict[str, Any]:
    """Extract rabies tag information."""
    rabies_tag = {}

    try:
        # Look for rabies tag in various locations
        rabies_selectors = [
            "text=/Rabies Tag Number/",
            "dt:has-text('Rabies Tag Number') + dd",
            "p:has-text('Rabies Tag Number') ~ p"
        ]

        for selector in rabies_selectors:
            try:
                element = page.locator(selector).first
                if element.count() > 0:
                    text = element.inner_text(timeout=1000).strip()
                    # Extract number from text like "Rabies Tag Number: 18654"
                    if ":" in text:
                        number_part = text.split(":", 1)[1].strip()
                        if number_part:
                            rabies_tag["number"] = number_part
                            break
            except:
                continue

    except Exception as e:
        print(f"Error extracting rabies tag: {e}")

    return rabies_tag


def extract_vaccination_history(page) -> List[Dict[str, Any]]:
    """Extract vaccination history."""
    vaccinations = []

    try:
        # Find Vaccination History section
        vacc_header = page.locator("h2:has-text('Vaccination History')")
        if vacc_header.count() == 0:
            return vaccinations

        # Look for vaccination entries - they are divs with border-l-8 border-green-600 directly
        vacc_entries = page.locator("h2:has-text('Vaccination History') ~ div.border-l-8.border-green-600")

        for i in range(vacc_entries.count()):
            entry = vacc_entries.nth(i)

            try:
                vacc_data = {}

                # Extract vaccine name from h3
                vaccine_name_elem = entry.locator("h3").first
                if vaccine_name_elem.count() > 0:
                    vaccine_name = vaccine_name_elem.inner_text(timeout=1000).strip()
                    vacc_data["vaccine"] = vaccine_name

                # Extract status and date from the status paragraph
                status_elem = entry.locator("p:has-text('–')").first
                if status_elem.count() > 0:
                    status_text = status_elem.inner_text(timeout=1000).strip()
                    # Format: "07/19/2025 – Completed"
                    if " – " in status_text:
                        date_part, status_part = status_text.split(" – ", 1)
                        vacc_data["date"] = date_part.strip()
                        vacc_data["status"] = status_part.strip()

                # Extract additional details from the grid
                grid_container = entry.locator(".grid.grid-cols-4").first
                if grid_container.count() > 0:
                    # Extract labels and values
                    labels = grid_container.locator("label")
                    values = grid_container.locator("p")

                    label_value_pairs = {}
                    for j in range(min(labels.count(), values.count())):
                        label = labels.nth(j).inner_text(timeout=1000).strip()
                        value = values.nth(j).inner_text(timeout=1000).strip()
                        label_value_pairs[label] = value

                    # Map to our schema
                    vacc_data["lot_number"] = label_value_pairs.get("Lot #", "")
                    vacc_data["route"] = label_value_pairs.get("Route", "")
                    vacc_data["expiration_date"] = label_value_pairs.get("Exp. Date", "")
                    vacc_data["site"] = label_value_pairs.get("Site", "")

                if vacc_data.get("vaccine"):
                    vaccinations.append(vacc_data)

            except Exception as e:
                print(f"Error extracting vaccination entry {i}: {e}")
                continue

    except Exception as e:
        print(f"Error extracting vaccination history: {e}")

    return vaccinations


def extract_treatments_due(page) -> List[Dict[str, Any]]:
    """Extract treatments currently due."""
    treatments_due = []

    try:
        # Find Treatments Next Due section
        treatments_header = page.locator("h2:has-text('Treatments Next Due')")
        if treatments_header.count() == 0:
            return treatments_due

        # Look for treatment tables
        treatment_tables = page.locator("h2:has-text('Treatments Next Due') ~ div table")

        for table_idx in range(treatment_tables.count()):
            table = treatment_tables.nth(table_idx)

            rows = table.locator("tbody tr")
            for i in range(rows.count()):
                row = rows.nth(i)
                cells = row.locator("td")

                if cells.count() >= 4:
                    treatment = cells.nth(0).inner_text(timeout=1000).strip()
                    dosage = cells.nth(1).inner_text(timeout=1000).strip()
                    frequency = cells.nth(2).inner_text(timeout=1000).strip()
                    due_date = cells.nth(3).inner_text(timeout=1000).strip()

                    # Determine status
                    status = "Due"
                    if "overdue" in due_date.lower():
                        status = "Overdue"
                        # Clean up the date
                        due_date = due_date.replace("(Overdue)", "").strip()

                    treatments_due.append({
                        "treatment": treatment,
                        "dosage": dosage,
                        "frequency": frequency,
                        "due_date": due_date,
                        "status": status
                    })

    except Exception as e:
        print(f"Error extracting treatments due: {e}")

    return treatments_due


def extract_treatment_history(page) -> List[Dict[str, Any]]:
    """Extract treatment history."""
    treatment_history = []

    try:
        # Find Treatment History section
        history_header = page.locator("h2:has-text('Treatment History')")
        if history_header.count() == 0:
            return treatment_history

        # Look for treatment entries
        treatment_entries = page.locator("h2:has-text('Treatment History') ~ div div.border-l-8")

        for i in range(treatment_entries.count()):
            entry = treatment_entries.nth(i)

            try:
                # Extract title/date line
                title_elem = entry.locator("h4").first
                title = title_elem.inner_text(timeout=1000).strip() if title_elem.count() > 0 else ""

                # Extract content
                content_elem = entry.locator("div.text-sm").first
                content = content_elem.inner_text(timeout=1000).strip() if content_elem.count() > 0 else ""

                if title and content:
                    # Parse treatment details from title and content
                    treatment_data = parse_treatment_entry(title, content)
                    if treatment_data:
                        treatment_history.append(treatment_data)

            except Exception as e:
                print(f"Error extracting treatment entry {i}: {e}")
                continue

    except Exception as e:
        print(f"Error extracting treatment history: {e}")

    return treatment_history


def parse_treatment_entry(title: str, content: str) -> Dict[str, Any]:
    """Parse a treatment entry from title and content."""
    treatment = {}

    try:
        # Extract treatment name and dates from title
        # Format: "Treatment Name - Start Date - End Date - Status"
        parts = title.split(" - ")
        if len(parts) >= 1:
            treatment["treatment"] = parts[0].strip()

        # Extract dates and status
        for part in parts[1:]:
            part = part.strip()
            if "/" in part and len(part.split("/")) == 3:  # Date format
                if "start_date" not in treatment:
                    treatment["start_date"] = part
                else:
                    treatment["end_date"] = part
            elif part in ["Completed", "In Progress", "Cancelled"]:
                treatment["status"] = part

        # Extract dosage and other details from content
        content_lower = content.lower()

        # Look for dosage patterns
        if "give" in content_lower and ("mg" in content_lower or "ml" in content_lower):
            # Extract dosage info
            treatment["dosage"] = extract_dosage_from_content(content)

        # Extract frequency
        if "daily" in content_lower or "sid" in content_lower:
            treatment["frequency"] = "Once daily"
        elif "twice" in content_lower or "bid" in content_lower:
            treatment["frequency"] = "Twice daily"
        elif "three times" in content_lower or "tid" in content_lower:
            treatment["frequency"] = "Three times daily"

        # Extract veterinarian if mentioned
        if "veterinarian:" in content_lower:
            vet_part = content.split("Veterinarian:", 1)[1].strip()
            treatment["veterinarian"] = vet_part.split("\n")[0].strip()

        # Store full notes
        treatment["notes"] = content

    except Exception as e:
        print(f"Error parsing treatment entry: {e}")

    return treatment


def extract_dosage_from_content(content: str) -> str:
    """Extract dosage information from treatment content."""
    # Look for patterns like "Give X mg" or "Give X ml"
    import re

    # Find dosage patterns
    dosage_patterns = [
        r'give\s+([\d.]+\s*(?:mg|ml|tablet|tab))',
        r'([\d.]+\s*(?:mg|ml|tablet|tab))\s+po',
        r'([\d.]+\s*(?:mg|ml|tablet|tab))\s+(?:po|orally)'
    ]

    for pattern in dosage_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return ""


def extract_diagnoses(page) -> List[Dict[str, Any]]:
    """Extract diagnoses information."""
    diagnoses = []

    try:
        # Look for Active Diagnoses and Resolved Diagnoses sections
        diagnosis_sections = ["Active Diagnoses", "Resolved Diagnoses"]

        for section_name in diagnosis_sections:
            section_header = page.locator(f"h2:has-text('{section_name}')")
            if section_header.count() == 0:
                continue

            # Find diagnosis entries - they are divs with border-l-8 border-green-600 directly
            diagnosis_entries = page.locator(f"h2:has-text('{section_name}') ~ div.border-l-8.border-green-600")

            for i in range(diagnosis_entries.count()):
                entry = diagnosis_entries.nth(i)

                try:
                    # Extract diagnosis name from h3
                    title_elem = entry.locator("h3").first
                    condition = title_elem.inner_text(timeout=1000).strip() if title_elem.count() > 0 else ""

                    # Extract status and date from the status paragraph
                    status_elem = entry.locator("p:has-text('–')").first
                    status = section_name.replace(" Diagnoses", "").lower()  # "active" or "resolved"
                    diagnosed_date = ""

                    if status_elem.count() > 0:
                        status_text = status_elem.inner_text(timeout=1000).strip()
                        # Format: "10/02/2025 – Active"
                        if " – " in status_text:
                            date_part, status_part = status_text.split(" – ", 1)
                            diagnosed_date = date_part.strip()
                            status = status_part.strip().lower()

                    # Extract additional details from the grid
                    grid_container = entry.locator(".grid.grid-cols-5").first
                    diagnosed_by = ""
                    notes = ""

                    if grid_container.count() > 0:
                        labels = grid_container.locator("label")
                        values = grid_container.locator("p")

                        for j in range(min(labels.count(), values.count())):
                            label = labels.nth(j).inner_text(timeout=1000).strip()
                            value = values.nth(j).inner_text(timeout=1000).strip()

                            if "Diagnosed by" in label:
                                diagnosed_by = value
                            elif "Notes" in label:
                                notes = value

                    if condition:
                        diagnosis_data = {
                            "condition": condition,
                            "category": categorize_diagnosis(condition, notes),
                            "status": status.capitalize(),
                            "diagnosed_date": diagnosed_date,
                            "veterinarian": diagnosed_by,
                            "description": notes
                        }
                        diagnoses.append(diagnosis_data)

                except Exception as e:
                    print(f"Error extracting diagnosis entry {i}: {e}")
                    continue

    except Exception as e:
        print(f"Error extracting diagnoses: {e}")

    return diagnoses


def parse_diagnosis_entry(title: str, content: str, section_name: str) -> Dict[str, Any]:
    """Parse a diagnosis entry."""
    diagnosis = {}

    try:
        # Determine status from section name
        if "Active" in section_name:
            diagnosis["status"] = "Active"
        elif "Resolved" in section_name:
            diagnosis["status"] = "Resolved"
        else:
            diagnosis["status"] = "Diagnosed"

        # Parse diagnosis condition from title
        diagnosis["condition"] = title.strip()

        # Categorize diagnosis
        diagnosis["category"] = categorize_diagnosis(title, content)

        # Extract dates if available
        # Look for date patterns in content
        import re
        date_pattern = r'(\d{1,2}/\d{1,2}/\d{4})'
        dates = re.findall(date_pattern, content)

        if len(dates) >= 1:
            diagnosis["diagnosed_date"] = dates[0]
        if len(dates) >= 2:
            diagnosis["resolved_date"] = dates[1]

        # Extract veterinarian if mentioned
        if "diagnosed by" in content.lower():
            vet_part = content.lower().split("diagnosed by")[1].strip()
            diagnosis["veterinarian"] = vet_part.split("\n")[0].strip()

        # Store description
        diagnosis["description"] = content

    except Exception as e:
        print(f"Error parsing diagnosis entry: {e}")

    return diagnosis


def categorize_diagnosis(title: str, content: str) -> str:
    """Categorize a diagnosis."""
    title_lower = title.lower()
    content_lower = content.lower()

    if "dental" in title_lower or "periodontal" in title_lower:
        return "Dental/Periodontal Disease"
    elif "heart" in title_lower or "cardiovascular" in title_lower or "murmur" in title_lower:
        return "Cardiovascular"
    elif "skin" in title_lower or "dermatitis" in title_lower:
        return "Skin"
    else:
        return "Other"


def extract_diagnostic_tests(page) -> List[Dict[str, Any]]:
    """Extract diagnostic tests history."""
    diagnostic_tests = []

    try:
        # Find Diagnostic Tests History section
        tests_header = page.locator("h2:has-text('Diagnostic Tests History')")
        if tests_header.count() == 0:
            return diagnostic_tests

        # Find test entries
        test_entries = page.locator("h2:has-text('Diagnostic Tests History') ~ div div.border-l-8")

        for i in range(test_entries.count()):
            entry = test_entries.nth(i)

            try:
                # Extract test name and date
                title_elem = entry.locator("h4").first
                title = title_elem.inner_text(timeout=1000).strip() if title_elem.count() > 0 else ""

                # Extract content/details
                content_elem = entry.locator("div.text-sm").first
                content = content_elem.inner_text(timeout=1000).strip() if content_elem.count() > 0 else ""

                if title and content:
                    test_data = parse_diagnostic_test_entry(title, content)
                    if test_data:
                        diagnostic_tests.append(test_data)

            except Exception as e:
                print(f"Error extracting diagnostic test entry {i}: {e}")
                continue

    except Exception as e:
        print(f"Error extracting diagnostic tests: {e}")

    return diagnostic_tests


def parse_diagnostic_test_entry(title: str, content: str) -> Dict[str, Any]:
    """Parse a diagnostic test entry."""
    test = {}

    try:
        # Parse test type and date from title
        # Format: "Test Type - Date - Status"
        parts = title.split(" - ")
        if len(parts) >= 1:
            test["test_type"] = parts[0].strip()

        # Extract date and status
        for part in parts[1:]:
            part = part.strip()
            if "/" in part and len(part.split("/")) == 3:  # Date format
                test["date"] = part
            elif part in ["Completed", "Pending", "Scheduled"]:
                test["status"] = part

        # Extract results from content
        test["results"] = content

        # Extract veterinarian if mentioned
        content_lower = content.lower()
        if "veterinarian:" in content_lower:
            vet_part = content.split("Veterinarian:", 1)[1].strip()
            test["veterinarian"] = vet_part.split("\n")[0].strip()

        # Store full notes
        test["notes"] = content

    except Exception as e:
        print(f"Error parsing diagnostic test entry: {e}")

    return test


def extract_physical_exams(page) -> List[Dict[str, Any]]:
    """Extract physical exam history."""
    physical_exams = []

    try:
        # Find Physical Exam History section
        exams_header = page.locator("h2:has-text('Physical Exam History')")
        if exams_header.count() == 0:
            return physical_exams

        # Find exam entries
        exam_entries = page.locator("h2:has-text('Physical Exam History') ~ div div.border-l-8")

        for i in range(exam_entries.count()):
            entry = exam_entries.nth(i)

            try:
                # Extract exam type and date
                title_elem = entry.locator("h4").first
                title = title_elem.inner_text(timeout=1000).strip() if title_elem.count() > 0 else ""

                # Extract content/details
                content_elem = entry.locator("div.text-sm").first
                content = content_elem.inner_text(timeout=1000).strip() if content_elem.count() > 0 else ""

                if title and content:
                    exam_data = parse_physical_exam_entry(title, content)
                    if exam_data:
                        physical_exams.append(exam_data)

            except Exception as e:
                print(f"Error extracting physical exam entry {i}: {e}")
                continue

    except Exception as e:
        print(f"Error extracting physical exams: {e}")

    return physical_exams


def parse_physical_exam_entry(title: str, content: str) -> Dict[str, Any]:
    """Parse a physical exam entry."""
    exam = {}

    try:
        # Parse exam type from title
        exam["exam_type"] = title.split("-")[0].strip() if "-" in title else title.strip()

        # Extract date and time if available
        import re
        datetime_pattern = r'(\d{1,2}/\d{1,2}/\d{4}\s*\|\s*\d{1,2}:\d{2}\s*(?:am|pm))'
        datetime_match = re.search(datetime_pattern, content, re.IGNORECASE)

        if datetime_match:
            exam["date"] = datetime_match.group(1).strip()

        # Extract veterinarian
        vet_patterns = [r'Examination By\s*([^\n]+)', r'Vet Exam By\s*([^\n]+)']
        for pattern in vet_patterns:
            vet_match = re.search(pattern, content, re.IGNORECASE)
            if vet_match:
                exam["veterinarian"] = vet_match.group(1).strip()
                break

        # Extract clinic
        clinic_patterns = [r'Clinic\s*([^\n]+)']
        for pattern in clinic_patterns:
            clinic_match = re.search(pattern, content, re.IGNORECASE)
            if clinic_match:
                exam["clinic"] = clinic_match.group(1).strip()
                break

        # Parse SOAP notes if present
        soap_patterns = {
            "subjective": r'Subjective\s*([^\n]+(?:\n(?!\s*(?:Objective|Assessment|Plan|$)).*)*)',
            "objective": r'Objective\s*([^\n]+(?:\n(?!\s*(?:Assessment|Plan|$)).*)*)',
            "assessment": r'Assessment\s*([^\n]+(?:\n(?!\s*(?:Plan|$)).*)*)',
            "plan": r'Plan\s*([^\n]+(?:\n(?!\s*$)).*)'
        }

        for soap_part, pattern in soap_patterns.items():
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                exam[soap_part] = match.group(1).strip()

    except Exception as e:
        print(f"Error parsing physical exam entry: {e}")

    return exam


def extract_procedures(page) -> List[Dict[str, Any]]:
    """Extract procedures/surgeries history."""
    procedures = []

    try:
        # Find Procedures/Surgeries History section
        procedures_header = page.locator("h2:has-text('Procedures/Surgeries History')")
        if procedures_header.count() == 0:
            return procedures

        # Find procedure entries
        procedure_entries = page.locator("h2:has-text('Procedures/Surgeries History') ~ div div.border-l-8")

        for i in range(procedure_entries.count()):
            entry = procedure_entries.nth(i)

            try:
                # Extract procedure name and date
                title_elem = entry.locator("h4").first
                title = title_elem.inner_text(timeout=1000).strip() if title_elem.count() > 0 else ""

                # Extract content/details
                content_elem = entry.locator("div.text-sm").first
                content = content_elem.inner_text(timeout=1000).strip() if content_elem.count() > 0 else ""

                if title and content:
                    procedure_data = parse_procedure_entry(title, content)
                    if procedure_data:
                        procedures.append(procedure_data)

            except Exception as e:
                print(f"Error extracting procedure entry {i}: {e}")
                continue

    except Exception as e:
        print(f"Error extracting procedures: {e}")

    return procedures


def parse_procedure_entry(title: str, content: str) -> Dict[str, Any]:
    """Parse a procedure entry."""
    procedure = {}

    try:
        # Parse procedure name and date from title
        # Format: "Procedure Name - Date - Status"
        parts = title.split(" - ")
        if len(parts) >= 1:
            procedure["procedure"] = parts[0].strip()

        # Extract date and status
        for part in parts[1:]:
            part = part.strip()
            if "/" in part and len(part.split("/")) == 3:  # Date format
                procedure["date"] = part
            elif part in ["Completed", "Scheduled", "Cancelled"]:
                procedure["status"] = part

        # Extract surgeon from content
        import re
        surgeon_patterns = [r'Surgeon\s*([^\n]+)', r'Performed by\s*([^\n]+)']
        for pattern in surgeon_patterns:
            surgeon_match = re.search(pattern, content, re.IGNORECASE)
            if surgeon_match:
                procedure["surgeon"] = surgeon_match.group(1).strip()
                break

        # Extract clinic
        clinic_patterns = [r'Clinic\s*([^\n]+)']
        for pattern in clinic_patterns:
            clinic_match = re.search(pattern, content, re.IGNORECASE)
            if clinic_match:
                procedure["clinic"] = clinic_match.group(1).strip()
                break

        # Store notes
        procedure["notes"] = content

    except Exception as e:
        print(f"Error parsing procedure entry: {e}")

    return procedure


def extract_medical_memos(page) -> List[Dict[str, Any]]:
    """Extract medical memos from the medical history section."""
    medical_memos = []

    try:
        # Find medical memos in the Complete Medical History section
        # Look for entries that have dates and are medical-related
        memo_selectors = [
            "h1:has-text('Complete Medical History') ~ div div.border-l-8",
            "h1:has-text('Complete Medical History') ~ div div:has-text('by')"
        ]

        for selector in memo_selectors:
            memo_elements = page.locator(selector)

            for i in range(memo_elements.count()):
                element = memo_elements.nth(i)

                try:
                    # Check if this looks like a medical memo (has date and author)
                    text_content = element.inner_text(timeout=1000)

                    # Look for date patterns and "by" keyword
                    if "/" in text_content and " by " in text_content.lower():
                        memo_data = parse_medical_memo(text_content)
                        if memo_data:
                            medical_memos.append(memo_data)

                except Exception:
                    continue

    except Exception as e:
        print(f"Error extracting medical memos: {e}")

    return medical_memos


def parse_medical_memo(content: str) -> Dict[str, Any]:
    """Parse a medical memo entry."""
    memo = {}

    try:
        # Split content by date and author
        lines = content.strip().split('\n')

        # First line should contain date and author
        if lines:
            first_line = lines[0].strip()
            if " by " in first_line:
                date_part, author_part = first_line.split(" by ", 1)
                memo["date"] = date_part.strip()
                memo["author"] = author_part.strip()
                memo["content"] = '\n'.join(lines[1:]).strip()

        if memo.get("content"):
            return memo

    except Exception as e:
        print(f"Error parsing medical memo: {e}")

    return {}