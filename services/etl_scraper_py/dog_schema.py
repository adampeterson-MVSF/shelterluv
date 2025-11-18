"""
New structured Dog schema definition.
This replaces the flat schema with nested, logical groupings.
"""

from typing import Any, Dict, List, Optional, Literal
from datetime import datetime


class DogSchema:
    """Structured Dog schema with nested fields."""

    @staticmethod
    def create_empty() -> Dict[str, Any]:
        """Create an empty dog record with all nested structures initialized."""
        return {
            # Identity
            "internalId": "",
            "publicId": "",
            "name": "",
            "type": "Dog",

            # Status & lifecycle
            "status": "UNKNOWN",
            "inFoster": False,
            "lastIntakeAt": None,
            "lastUpdatedAt": None,

            # Physical
            "physical": {
                "breed": "",
                "ageDays": 0,
                "dob": None,
                "sex": "Unknown",
                "sizeLabel": "",
                "color": "",
                "pattern": "",
                "weightLbs": None,
                "altered": None,
            },

            # Location
            "location": {
                "raw": {},
                "label": None,
            },

            # People / relationships
            "foster": {
                "inFoster": False,
                "person": None,
            },

            # Media
            "media": {
                "coverPhoto": None,
                "photos": [],
                "videos": [],
            },

            # Attributes & tags
            "attributes": {
                "raw": [],
                "compatibility": {},
            },

            # Medical / identification
            "medical": {
                "microchips": [],
            },

            # Content
            "content": {
                "description": "",
            },

            # Admin / misc
            "admin": {
                "adoptionFeeGroup": None,
                "litterGroupId": None,
                "previousIds": [],
            },

            # Source metadata
            "source": {
                "lastIntakeUnixTime": None,
                "lastUpdatedUnixTime": None,
                "dobUnixTime": None,
                "raw": {},
                "syncedAt": datetime.utcnow().isoformat(),
            },
        }


def from_shelterluv_api(animal_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform ShelterLuv API response into structured Dog schema.

    Args:
        animal_json: Raw animal data from ShelterLuv API

    Returns:
        Structured dog record matching the new nested schema
    """
    dog = DogSchema.create_empty()

    # Identity
    dog["internalId"] = animal_json.get("Internal-ID", "")
    dog["publicId"] = animal_json.get("ID", "")
    dog["name"] = animal_json.get("Name", "")
    dog["type"] = animal_json.get("Type", "Dog")

    # Status & lifecycle
    dog["status"] = _normalize_status(animal_json.get("Status", "UNKNOWN"))
    dog["inFoster"] = animal_json.get("InFoster", False)
    dog["lastIntakeAt"] = _unix_to_datetime(animal_json.get("LastIntakeUnixTime"))
    dog["lastUpdatedAt"] = _unix_to_datetime(animal_json.get("LastUpdatedUnixTime"))

    # Physical
    dog["physical"]["breed"] = animal_json.get("Breed", "")
    # Calculate age from DOB instead of trusting the Age field directly
    dob_unix = animal_json.get("DOBUnixTime")
    dog["physical"]["ageDays"] = _calculate_age_days_from_dob(dob_unix)
    dog["physical"]["dob"] = _unix_to_datetime(dob_unix)
    dog["physical"]["sex"] = _normalize_sex(animal_json.get("Sex", "Unknown"))
    dog["physical"]["sizeLabel"] = animal_json.get("Size", "")
    dog["physical"]["color"] = animal_json.get("Color", "")
    dog["physical"]["pattern"] = animal_json.get("Pattern") or ""
    dog["physical"]["weightLbs"] = _parse_weight(animal_json.get("CurrentWeightPounds"))
    dog["physical"]["altered"] = _normalize_altered(animal_json.get("Altered"))

    # Location
    dog["location"]["raw"] = animal_json.get("CurrentLocation", {})
    dog["location"]["label"] = _derive_location_label(animal_json.get("CurrentLocation"))

    # People / relationships
    associated_person = animal_json.get("AssociatedPerson")
    if associated_person:
        dog["foster"]["inFoster"] = dog["inFoster"]
        dog["foster"]["person"] = {
            "firstName": associated_person.get("FirstName"),
            "lastName": associated_person.get("LastName"),
            "relationshipType": associated_person.get("RelationshipType"),
            "outDate": _unix_to_datetime(associated_person.get("OutDateUnixTime")),
        }

    # Media
    dog["media"]["photos"] = animal_json.get("Photos", [])
    dog["media"]["videos"] = animal_json.get("Videos", [])
    dog["media"]["coverPhoto"] = animal_json.get("CoverPhoto") or (
        dog["media"]["photos"][0] if dog["media"]["photos"] else None
    )

    # Attributes
    dog["attributes"]["raw"] = [
        {
            "attributeName": attr.get("AttributeName", ""),
            "internalId": attr.get("Internal-ID", ""),
            "publish": attr.get("Publish", "No"),
        }
        for attr in animal_json.get("Attributes", [])
    ]

    # Medical
    dog["medical"]["microchips"] = [
        {
            "id": chip.get("Id", ""),
            "issuer": chip.get("Issuer"),
            "implantedAt": _unix_to_datetime(chip.get("ImplantUnixTime")),
        }
        for chip in animal_json.get("Microchips", [])
    ]

    # Content
    dog["content"]["description"] = animal_json.get("Description", "")

    # Admin
    dog["admin"]["adoptionFeeGroup"] = _normalize_adoption_fee_group(animal_json.get("AdoptionFeeGroup"))
    dog["admin"]["litterGroupId"] = animal_json.get("LitterGroupId")
    dog["admin"]["previousIds"] = [
        {
            "idValue": prev_id.get("IdValue", ""),
            "issuingShelter": prev_id.get("IssuingShelter"),
            "type": prev_id.get("Type", ""),
        }
        for prev_id in animal_json.get("PreviousIds", [])
    ]

    # Source metadata
    dog["source"]["lastIntakeUnixTime"] = _to_number_or_none(animal_json.get("LastIntakeUnixTime"))
    dog["source"]["lastUpdatedUnixTime"] = _to_number_or_none(animal_json.get("LastUpdatedUnixTime"))
    dog["source"]["dobUnixTime"] = _to_number_or_none(animal_json.get("DOBUnixTime"))
    dog["source"]["raw"] = animal_json

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

    # Check for available variations (including hospice)
    if any(keyword in status_lower for keyword in ["available", "hospice"]):
        return "available"

    # Check for pending variations
    if any(keyword in status_lower for keyword in ["pending", "unavailable"]):
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


def _normalize_sex(sex: str) -> Literal["Male", "Female", "Unknown"]:
    """Normalize sex values."""
    if sex.lower() in ["male", "m"]:
        return "Male"
    elif sex.lower() in ["female", "f"]:
        return "Female"
    else:
        return "Unknown"


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
