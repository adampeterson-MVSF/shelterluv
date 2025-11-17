"""
Tests for cross-language safety consistency.

Ensures JS and Python safety mappings are mechanically equivalent.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from config_loader import get_project_safety


class TestCrossLanguageSafety:
    """Test that JS and Python safety logic produce identical results."""

    def test_python_safety_map_structure(self):
        """Test that Python safety map has expected structure."""
        safety = get_project_safety()

        assert isinstance(safety, dict)
        assert len(safety) > 0

        # Check structure of each project entry
        for project_id, info in safety.items():
            assert isinstance(project_id, str)
            assert isinstance(info, dict)
            assert "is_safe" in info
            assert isinstance(info["is_safe"], bool)

    def test_js_python_safety_consistency(self):
        """Test that JS and Python safety decisions are identical for all projects."""
        # Get Python safety map
        python_safety = get_project_safety()

        # Get profile map to simulate JS logic
        from config_loader import get_normalized_profile_map
        profile_map = get_normalized_profile_map()

        # Simulate JS isSafeProject logic
        js_safety = {}
        for project_id in python_safety.keys():
            # A project is safe if ANY profile that maps to it is safe
            is_safe = any(
                profile_info["gcp_project"] == project_id and profile_info["is_safe"]
                for profile_info in profile_map.values()
            )
            js_safety[project_id] = {"is_safe": is_safe}

        # Compare the maps
        assert python_safety == js_safety, (
            "JS and Python safety maps differ!\n"
            f"Python: {python_safety}\n"
            f"JS: {js_safety}\n"
            f"Profile map: {profile_map}"
        )

    def test_no_duplicate_projects_in_safety_map(self):
        """Test that no project appears multiple times in safety map."""
        safety = get_project_safety()
        project_ids = list(safety.keys())

        # Check for duplicates
        assert len(project_ids) == len(set(project_ids)), (
            f"Duplicate project IDs found in safety map: {project_ids}"
        )

    def test_all_projects_have_valid_env_profiles(self):
        """Test that all projects in safety map can be mapped back to valid env profiles."""
        from config import EnvProfile
        from config_loader import get_normalized_profile_map

        safety = get_project_safety()
        profile_map = get_normalized_profile_map()
        valid_profiles = {e.value for e in EnvProfile}

        # Check that for each project, there's at least one profile that maps to it
        for project_id in safety.keys():
            profiles_for_project = [
                profile_name for profile_name, profile_info in profile_map.items()
                if profile_info["gcp_project"] == project_id
            ]
            assert len(profiles_for_project) > 0, (
                f"Project '{project_id}' has no corresponding profiles in config"
            )
            assert all(profile in valid_profiles for profile in profiles_for_project), (
                f"Project '{project_id}' maps to invalid profiles: {profiles_for_project}. "
                f"Valid profiles: {sorted(valid_profiles)}"
            )

    def test_safety_consistency_with_config(self):
        """Test that safety map is consistent with raw config data."""
        from config_loader import get_python_env_profiles, get_safe_profiles

        python_profiles = get_python_env_profiles()
        safe_profiles = set(get_safe_profiles())
        safety = get_project_safety()

        # Every python_env_profile should appear in safety map
        for profile_name, profile_config in python_profiles.items():
            project_id = profile_config["gcp_project"]
            assert project_id in safety, (
                f"Project '{project_id}' from profile '{profile_name}' not found in safety map"
            )

            # A project is safe if ANY profile that maps to it is safe
            expected_is_safe = any(
                p_config["gcp_project"] == project_id and p_name in safe_profiles
                for p_name, p_config in python_profiles.items()
            )

            assert safety[project_id]["is_safe"] == expected_is_safe, (
                f"Safety for project '{project_id}' doesn't match config. "
                f"Expected: {expected_is_safe}, Got: {safety[project_id]['is_safe']}"
            )
