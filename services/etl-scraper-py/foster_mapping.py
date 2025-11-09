"""
Foster and event mapping functions for ETL pipeline.

Handles building foster parent mappings and event associations.
Separated from enrichment.py to keep file sizes manageable.
"""

from typing import Dict, Any, List
from datetime import datetime
import re


def build_foster_maps(events: List[Dict[str, Any]], people: List[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
    """
    Build mapping from animal internal ID to current foster person information.
    Uses state machine approach: processes events chronologically to maintain current foster state.

    State transitions:
    - 'Foster' event: sets current foster person for the animal
    - 'FosterReturn' event: clears current foster person for the animal

    Returns animal_to_foster_dict: {animal_id: {field: value}} for animals currently in foster care.
    """
    # Build person lookup
    person_by_id = {str(p.get('ID', '')): p for p in people if p.get('ID')}

    # Track current foster state per animal
    current_fosters: Dict[str, Dict[str, str]] = {}

    # Sort events by date ASC (chronological order) to process state transitions correctly
    sorted_events = sorted(events, key=lambda e: e.get('Date', ''))

    for event in sorted_events:
        event_type = event.get('Type', '')
        animal_id = str(event.get('AnimalID', ''))

        if not animal_id:
            continue

        if event_type == 'Foster':
            # Set foster person for this animal
            person_id = str(event.get('PersonID', ''))
            person = person_by_id.get(person_id)
            if person:
                current_fosters[animal_id] = {
                    'FosterName': person.get('Name', ''),
                    'FosterPhone': person.get('Phone', ''),
                    'FosterEmail': person.get('Email', '')
                }

        elif event_type == 'FosterReturn':
            # Clear foster person for this animal (returned from foster care)
            current_fosters.pop(animal_id, None)

    return current_fosters


def build_event_maps(events: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Build mapping from animal IDs to event participation information.

    Args:
        events: List of event dictionaries with animal associations

    Returns:
        Dict mapping animal Internal-ID to event info dict with keys:
        - '_event_types': List of event types the animal has participated in
        - '_last_event_date': Most recent event date
        - '_event_count': Total number of events
    """
    event_map = {}

    for event in events:
        animal_id = event.get('Animal-Internal-ID')
        if not animal_id:
            continue

        event_type = event.get('Type', '').strip()
        event_date = event.get('Date', '')

        if animal_id not in event_map:
            event_map[animal_id] = {
                '_event_types': [],
                '_last_event_date': None,
                '_event_count': 0
            }

        info = event_map[animal_id]

        # Add event type if not already present
        if event_type and event_type not in info['_event_types']:
            info['_event_types'].append(event_type)

        # Update last event date
        if event_date and (not info['_last_event_date'] or event_date > info['_last_event_date']):
            info['_last_event_date'] = event_date

        # Increment count
        info['_event_count'] += 1

    return event_map
