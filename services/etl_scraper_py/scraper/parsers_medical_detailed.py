"""
Detailed medical parsing functions for ShelterLuv scraper.

Handles extraction of comprehensive medical data including vaccinations, treatments,
diagnoses, tests, exams, and procedures from the Complete Medical History page.
"""

from .parsers_medical import extract_medical_history

# Re-export the unified function for backward compatibility
_extract_medical_history = extract_medical_history
