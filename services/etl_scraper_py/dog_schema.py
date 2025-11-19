"""
Dog schema definition using typed structure from JSON schema.
"""

from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
from dog_types import Dog


class DogSchema:
    """Structured Dog schema with nested fields."""

    @staticmethod
    def create_empty() -> Dog:
        """Create an empty dog record with JSON schema field names initialized."""
        return {
            # Required identity fields
            "Internal-ID": "",
            "ID": "",
            "Name": "",
            "Status": "UNKNOWN",
            "AgeYears": 0.0,
            "AgeDisplay": "",
            "IsInCustody": False,
            "IsAvailableForAdoption": False,
            "IsHospice": False,
            "IsEventDog": False,
            "PersonalityNotes": "",
            "IntakeNotes": "",
            "MedicalNotes": "",

            # Optional fields with defaults
            "Breed": "",
            "Size": "UNKNOWN",
            "Gender": "Male",  # Default to avoid None
            "Description": "",
            "Photos": [],
            "CaseManager": "",
            "MemosRawHTML": "",
            "MedicalHistory": {},
            "AdoptionCategory": "",
            "MedicalCategory": "",
            "BehaviorCategory": "",
            "VolunteerCategory": "",
            "FullAnimalProfile": "",
            "Treatments": [],
            "IntakeDate": "",
            "Location": "",
            "Stage": "",
            "Weight": "",
            "FosterName": "",
            "FosterPhone": "",
            "FosterEmail": "",
            "ScrapeError": "",
            "Attributes": [],
            "BehavioralAttributes": [],
            "PhysicalAttributes": [],
            "Species": "",
            "Color": "",
            "Pattern": "",
            "DistinguishingMarks": "",
            "AdoptionPrice": "",
            "MicrochipNumber": "",
            "MicrochipIssuer": "",
            "MicrochipImplantDate": "",
            "AlteredBeforeArrival": "",
            "AlteredInCare": "",
            "AgeGroup": "",
            "EstBirthdate": "",
            "IntakeType": "",
            "IntakeSubtype": "",
            "OutcomeType": "",
            "OutcomeSubtype": "",
            "AsilomarIntake": "",
            "AsilomarOutcome": "",
            "ConditionAtIntake": "",
            "JurisdictionIntake": "",
            "JurisdictionOutcome": "",
            "RabiesTagNumber": "",
            "EventHistory": [],
            "WeightHistory": [],
            "CategoryHistory": [],
            "BehavioralAssessments": [],
            "CompatibilityWarnings": [],
            "AttachedDocuments": [],
            "PreviousShelterId": "",
            "PreviousShelterType": "",
            "PreviousShelterIssuer": "",
            "Disclaimers": [],
            "WebsiteMemo": {},
            "MicrochipInfo": {},
            "RabiesTag": {},
            "VaccinationHistory": [],
            "TreatmentsDue": [],
            "TreatmentHistory": [],
            "Diagnoses": [],
            "DiagnosticTests": [],
            "PhysicalExams": [],
            "Procedures": [],
            "MedicalMemos": [],
        }


def from_shelterluv_api(animal_json: Dict[str, Any]) -> Dog:
    """
    Transform ShelterLuv API response into Dog schema with JSON field names.

    Args:
        animal_json: Raw animal data from ShelterLuv API

    Returns:
        Dog record matching the JSON schema structure
    """
    dog = DogSchema.create_empty()

    # Identity - use JSON schema field names
    dog["Internal-ID"] = animal_json.get("Internal-ID", "")
    dog["ID"] = animal_json.get("ID", "")
    dog["Name"] = animal_json.get("Name", "")

    # Status
    dog["Status"] = _normalize_status(animal_json.get("Status", "UNKNOWN"))

    # Basic info
    dog["Breed"] = animal_json.get("Breed", "")
    dog["Size"] = animal_json.get("Size", "UNKNOWN")
    dog["Gender"] = _normalize_sex(animal_json.get("Sex", "Male"))
    dog["Description"] = animal_json.get("Description", "")
    dog["Photos"] = animal_json.get("Photos", [])
    dog["IntakeDate"] = animal_json.get("IntakeDate", "")
    dog["Location"] = animal_json.get("Location", "")
    dog["Stage"] = animal_json.get("Stage", "")
    dog["Weight"] = str(animal_json.get("CurrentWeightPounds", ""))

    # Derived fields - calculate from API data
    dob_unix = animal_json.get("DOBUnixTime")
    age_days = _calculate_age_days_from_dob(dob_unix)
    dog["AgeYears"] = age_days / 365.25 if age_days else 0.0
    dog["AgeDisplay"] = _calculate_age_display(age_days)

    # Status flags - derive from available data
    dog["IsInCustody"] = True  # Assume all API data is for dogs in custody
    dog["IsAvailableForAdoption"] = dog["Status"] == "AVAILABLE"
    dog["IsHospice"] = False  # Would need more logic to determine
    dog["IsEventDog"] = False  # Would need more logic to determine

    # Notes - initialize as empty, will be filled by scraping
    dog["PersonalityNotes"] = ""
    dog["IntakeNotes"] = ""
    dog["MedicalNotes"] = ""

    # Foster information - derive from AssociatedPerson if available
    associated_person = animal_json.get("AssociatedPerson")
    if associated_person and associated_person.get("RelationshipType") == "Foster":
        dog["FosterName"] = f"{associated_person.get('FirstName', '')} {associated_person.get('LastName', '')}".strip()
        # Phone and email would need to be looked up separately

    return dog


def _unix_to_datetime(unix_time: Optional[int]) -> Optional[str]:
    """Convert Unix timestamp to ISO format datetime string."""
    if unix_time is None:
        return None
    try:
        dt = datetime.fromtimestamp(unix_time)
        return dt.isoformat()
    except (ValueError, TypeError):
        return None


def _to_number_or_none(value: Any) -> Optional[int]:
    """Convert value to number or return None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    return None


def _normalize_status(status: str) -> str:
    """Normalize status values from ShelterLuv API."""
    if not status:
        return "unknown"

    # Clean and normalize the status string
    status = status.strip().upper()

    # Direct mappings for exact matches
    status_map = {
        "AVAILABLE": "available",
        "ADOPTED": "adopted",
        "PENDING": "pending",
        "HOLD": "hold",
        "IN CUSTODY": "in_custody",
    }

    if status in status_map:
        return status_map[status]

    # Handle complex statuses with keywords
    status_lower = status.lower()

    # Check for available variations - strictly map Headquarters Available and Foster Available to AVAILABLE
    if any(keyword in status_lower for keyword in ["headquarters available", "foster available", "available", "hospice"]):
        return "available"

    # Check for pending variations - keep all Pending... variants as PENDING
    if "pending" in status_lower:
        return "pending"

    # Check for adopted variations
    if "adopted" in status_lower:
        return "adopted"

    # Check for hold variations
    if "hold" in status_lower:
        return "hold"

    # Check for in custody variations
    if any(keyword in status_lower for keyword in ["custody", "intake"]):
        return "in_custody"

    # Default to unknown for unrecognized statuses
    return "unknown"


def _normalize_adoption_fee_group(fee_group: Any) -> Optional[str]:
    """Normalize adoption fee group from API response."""
    if fee_group is None:
        return None

    if isinstance(fee_group, str):
        return fee_group

    if isinstance(fee_group, dict):
        # Extract name from object like {"Id": 15667, "Name": "Seniors for Seniors Adoption", ...}
        return fee_group.get("Name")

    # For other types, convert to string
    return str(fee_group)


def _normalize_sex(sex: str) -> Literal["Male", "Female"]:
    """Normalize sex values."""
    if sex.lower() in ["male", "m"]:
        return "Male"
    elif sex.lower() in ["female", "f"]:
        return "Female"
    else:
        return "Male"  # Default fallback


def _calculate_age_display(age_days: int) -> str:
    """Calculate human-readable age display from days."""
    if age_days == 0:
        return "Unknown"

    years = age_days // 365
    months = (age_days % 365) // 30
    weeks = (age_days % 365) // 7
    days = age_days % 7

    if years > 0:
        if months > 0:
            return f"{years} years {months} months"
        else:
            return f"{years} years"
    elif months > 0:
        if weeks > 0:
            return f"{months} months {weeks} weeks"
        else:
            return f"{months} months"
    elif weeks > 0:
        if days > 0:
            return f"{weeks} weeks {days} days"
        else:
            return f"{weeks} weeks"
    else:
        return f"{days} days"


def _parse_weight(weight_str: Optional[str]) -> Optional[float]:
    """Parse weight string to float pounds."""
    if not weight_str:
        return None
    try:
        # Handle various formats like "16 lbs", "7.3 kg", etc.
        weight_str = weight_str.lower().strip()
        if "lbs" in weight_str or "lb" in weight_str:
            return float(weight_str.split()[0])
        elif "kg" in weight_str:
            # Convert kg to lbs
            kg = float(weight_str.split()[0])
            return kg * 2.20462
        else:
            # Assume it's already in lbs
            return float(weight_str)
    except (ValueError, IndexError):
        return None


def _calculate_age_days_from_dob(dob_unix: Optional[int]) -> int:
    """Calculate age in days from Unix timestamp DOB."""
    if not dob_unix:
        return 0

    try:
        from datetime import datetime
        dob = datetime.fromtimestamp(dob_unix)
        now = datetime.now()
        age_delta = now - dob
        return max(0, age_delta.days)  # Ensure non-negative
    except (ValueError, TypeError, OverflowError):
        return 0


def _normalize_altered(altered: Optional[str]) -> Optional[bool]:
    """Normalize altered status to boolean."""
    if altered is None:
        return None
    return altered.lower() == "yes"


def _derive_location_label(current_location: Optional[Dict[str, Any]]) -> Optional[str]:
    """Derive a display label from CurrentLocation object."""
    if not current_location:
        return None

    location_type = current_location.get("LocationType")
    if location_type == "Foster Home":
        return "Foster home"
    elif location_type == "HQ":
        return "Muttville HQ"
    else:
        return location_type or "Unknown"
