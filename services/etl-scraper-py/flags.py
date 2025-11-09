"""
Derived flag computation for ETL pipeline.

Handles computation of boolean flags from raw dog data.
Separated from enrichment.py to keep file sizes manageable.
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class FlagsConfig:
    """Configuration for derived flag computation."""
    # Terminal statuses that indicate a dog is no longer in custody
    terminal_statuses: List[str]

    # Active statuses that generally indicate custody
    active_statuses: List[str]

    # Keywords for hospice detection
    hospice_keywords: List[str]

    # Keywords for event dog detection
    event_keywords: List[str]

    # Event types that indicate event participation
    event_types: List[str]


# Default configuration instance
DEFAULT_FLAGS_CONFIG = FlagsConfig(
    terminal_statuses=['ADOPTED'],
    active_statuses=['AVAILABLE', 'PENDING', 'HOLD', 'UNKNOWN'],
    hospice_keywords=['hospice', 'palliative', 'comfort care', 'end of life'],
    event_keywords=['event', 'outreach', 'adoption event', 'demonstration', 'education'],
    event_types=['Event', 'Adoption Event', 'Outreach', 'Showcase']
)


def compute_derived_flags(dog: Dict[str, Any], config: FlagsConfig = DEFAULT_FLAGS_CONFIG) -> Dict[str, Any]:
    """Compute all derived boolean flags."""
    result = dict(dog)

    status = result.get('Status', 'UNKNOWN')

    # Custody and availability flags
    result['IsInCustody'] = compute_is_in_custody(status, result, config)
    result['IsAvailableForAdoption'] = compute_is_available_for_adoption(status)

    # Hospice and event flags
    result['IsHospice'] = compute_is_hospice(result, config)
    result['IsEventDog'] = compute_is_event_dog(result, config)

    return result


def compute_custody(status: str, foster_state: str = None, api_in_custody_flag: bool = None,
                   config: FlagsConfig = DEFAULT_FLAGS_CONFIG) -> bool:
    """
    Compute whether a dog is currently in Muttville's custody.
    Single source of truth for custody logic.

    Args:
        status: Normalized status (AVAILABLE, ADOPTED, etc.)
        foster_state: Current foster status ('fostered', 'returned', None)
        api_in_custody_flag: Any API-provided custody indicator
        config: Configuration for flag computation

    Returns:
        bool: True if dog is in custody, False otherwise
    """
    # Terminal statuses mean the dog is no longer in custody
    if status in config.terminal_statuses:
        return False

    # Non-terminal statuses generally indicate custody
    if status in config.active_statuses:
        return True

    # Fallback: assume in custody if we have foster state or API flag
    if foster_state == 'fostered' or api_in_custody_flag:
        return True

    return False


def compute_is_in_custody(status: str, dog_data: Dict[str, Any], config: FlagsConfig = DEFAULT_FLAGS_CONFIG) -> bool:
    """
    Compute IsInCustody.

    Since we now source all animals from ShelterLuv's "In Custody" view,
    all animals in our ETL pipeline are guaranteed to be in custody.
    This field exists for schema compatibility and frontend logic.
    """
    foster_state = dog_data.get('FosterState')
    api_in_custody_flag = dog_data.get('InCustody')  # API field if present

    return compute_custody(status, foster_state, api_in_custody_flag, config)


def compute_is_available_for_adoption(status: str) -> bool:
    """
    Compute IsAvailableForAdoption from status.

    This is the single source of truth for adoption availability logic.
    Frontend should use this computed field, not re-encode status semantics.
    """
    # Only AVAILABLE status means actively available for adoption
    return status == 'AVAILABLE'


def compute_is_hospice(dog: Dict[str, Any], config: FlagsConfig = DEFAULT_FLAGS_CONFIG) -> bool:
    """
    Compute IsHospice flag.

    A dog is considered hospice if they have hospice-related keywords
    in their attributes, categories, or other metadata.
    """
    fields_to_check = [
        dog.get('AdoptionCategory', ''),
        dog.get('MedicalCategory', ''),
        dog.get('BehaviorCategory', ''),
        dog.get('Attributes', []),
        dog.get('Description', ''),
        dog.get('MedicalNotes', '')
    ]

    # Flatten attributes list if it's a list
    if isinstance(fields_to_check[3], list):
        fields_to_check[3] = ' '.join(fields_to_check[3])

    # Convert all to strings and check for keywords
    text_to_check = ' '.join(str(field).lower() for field in fields_to_check)

    return any(keyword in text_to_check for keyword in config.hospice_keywords)


def compute_is_event_dog(dog: Dict[str, Any], config: FlagsConfig = DEFAULT_FLAGS_CONFIG) -> bool:
    """
    Compute IsEventDog flag.

    A dog participates in events if they have event-related keywords
    or are associated with specific event types.
    """
    # Check if event_info was provided with event flags
    event_types = dog.get('_event_types', [])
    if event_types:
        return any(event_type in config.event_types for event_type in event_types)

    # Fallback: check other fields for event indicators
    fields_to_check = [
        dog.get('AdoptionCategory', ''),
        dog.get('BehaviorCategory', ''),
        dog.get('Attributes', []),
        dog.get('Description', ''),
        dog.get('PersonalityNotes', '')
    ]

    # Flatten attributes list if it's a list
    if isinstance(fields_to_check[2], list):
        fields_to_check[2] = ' '.join(fields_to_check[2])

    # Convert all to strings and check for keywords
    text_to_check = ' '.join(str(field).lower() for field in fields_to_check)

    return any(keyword in text_to_check for keyword in config.event_keywords)
