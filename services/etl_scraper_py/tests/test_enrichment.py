"""
Tests for enrichment logic, particularly foster mapping and structured notes parsing.
Tests _build_foster_maps for correct behavior with ordered and out-of-order events.
Tests memo parsing functions from scraper.parsers for keyword-based categorization.
"""

import pytest

from foster_mapping import build_foster_maps

# Note: Tests use parse_memos_by_type_pure directly, not ShelterLuvParsers class


class TestFosterMapping:
    """Test foster parent mapping from events and people data."""

    def test_single_foster_assignment(self):
        """Test basic foster assignment."""
        events = [{"Type": "Foster", "AnimalID": "123", "PersonID": "456", "Date": "2024-01-01"}]
        people = [
            {"ID": "456", "Name": "John Doe", "Phone": "555-0123", "Email": "john@example.com"}
        ]

        animal_to_foster = build_foster_maps(events, people)

        assert "123" in animal_to_foster
        assert animal_to_foster["123"]["FosterName"] == "John Doe"
        assert animal_to_foster["123"]["FosterPhone"] == "555-0123"
        assert animal_to_foster["123"]["FosterEmail"] == "john@example.com"

    def test_multiple_fosters_chronological_state_machine(self):
        """Test multiple foster assignments processed chronologically."""
        events = [
            {"Type": "Foster", "AnimalID": "123", "PersonID": "456", "Date": "2024-01-01"},
            {
                "Type": "Foster",
                "AnimalID": "123",
                "PersonID": "789",
                "Date": "2024-02-01",  # Later date
            },
        ]
        people = [
            {"ID": "456", "Name": "John Doe", "Phone": "555-0123", "Email": "john@example.com"},
            {"ID": "789", "Name": "Jane Smith", "Phone": "555-0456", "Email": "jane@example.com"},
        ]

        animal_to_foster = build_foster_maps(events, people)

        # Should have Jane Smith as the current foster (last chronological assignment)
        assert animal_to_foster["123"]["FosterName"] == "Jane Smith"

    def test_events_processed_chronologically(self):
        """Test that events are processed chronologically (state machine maintains current state)."""
        # Events in reverse chronological order in input
        events = [
            {
                "Type": "Foster",
                "AnimalID": "123",
                "PersonID": "789",
                "Date": "2024-02-01",  # Later date
            },
            {
                "Type": "Foster",
                "AnimalID": "123",
                "PersonID": "456",
                "Date": "2024-01-01",  # Earlier date
            },
        ]
        people = [
            {"ID": "456", "Name": "John Doe", "Phone": "555-0123", "Email": "john@example.com"},
            {"ID": "789", "Name": "Jane Smith", "Phone": "555-0456", "Email": "jane@example.com"},
        ]

        animal_to_foster = build_foster_maps(events, people)

        # Should process chronologically: first Foster (John), then Foster (Jane) - Jane wins
        assert animal_to_foster["123"]["FosterName"] == "Jane Smith"

    def test_foster_return_state_machine(self):
        """Test Foster → FosterReturn → Foster sequence (state machine behavior)."""
        events = [
            {
                "Type": "Foster",
                "AnimalID": "123",
                "PersonID": "456",
                "Date": "2024-01-01",  # First foster
            },
            {
                "Type": "FosterReturn",
                "AnimalID": "123",
                "Date": "2024-02-01",  # Returned from foster
            },
            {
                "Type": "Foster",
                "AnimalID": "123",
                "PersonID": "789",
                "Date": "2024-03-01",  # Re-fostered
            },
        ]
        people = [
            {"ID": "456", "Name": "John Doe", "Phone": "555-0123", "Email": "john@example.com"},
            {"ID": "789", "Name": "Jane Smith", "Phone": "555-0456", "Email": "jane@example.com"},
        ]

        animal_to_foster = build_foster_maps(events, people)

        # After FosterReturn, should have Jane Smith (final foster state)
        assert animal_to_foster["123"]["FosterName"] == "Jane Smith"

    def test_foster_return_clears_foster(self):
        """Test that FosterReturn clears foster state."""
        events = [
            {"Type": "Foster", "AnimalID": "123", "PersonID": "456", "Date": "2024-01-01"},
            {"Type": "FosterReturn", "AnimalID": "123", "Date": "2024-02-01"},
        ]
        people = [
            {"ID": "456", "Name": "John Doe", "Phone": "555-0123", "Email": "john@example.com"}
        ]

        animal_to_foster = build_foster_maps(events, people)

        # After FosterReturn, should not be in foster care
        assert "123" not in animal_to_foster

    def test_missing_person_data(self):
        """Test handling when person data is missing."""
        events = [
            {
                "Type": "Foster",
                "AnimalID": "123",
                "PersonID": "999",  # Person doesn't exist
                "Date": "2024-01-01",
            }
        ]
        people = [{"ID": "456", "Name": "John Doe"}]  # Different person

        animal_to_foster = build_foster_maps(events, people)

        # Should not have foster info when person is missing
        assert "123" not in animal_to_foster

    def test_empty_inputs(self):
        """Test handling of empty event/people lists."""
        animal_to_foster = build_foster_maps([], [])

        assert animal_to_foster == {}

    def test_malformed_events(self):
        """Test handling of malformed event data."""
        events = [
            {"Type": "Foster", "Date": "2024-01-01"},  # Missing AnimalID
            {"AnimalID": "123", "Date": "2024-01-01"},  # Missing Type
        ]
        people = []

        animal_to_foster = build_foster_maps(events, people)

        # Should handle gracefully without crashing
        assert isinstance(animal_to_foster, dict)


class TestStructuredNotesParsing:
    """Test structured notes parsing from raw HTML memos."""

    def test_empty_memos(self):
        """Test handling of empty memos."""
        from scraper.parsers import parse_memos_by_type_pure

        result = parse_memos_by_type_pure("")
        assert result["PersonalityNotes"] == "Not Available"
        assert result["IntakeNotes"] == ""
        assert result["MedicalNotes"] == "Not Available"

    def test_personality_keywords(self):
        """Test categorization of personality-related notes."""
        from scraper.parsers import parse_memos_by_type_pure

        memos = """
        <p>2024-01-15</p>
        <p>Personality: Very friendly and playful. Shows calm temperament around other dogs.</p>
        """
        result = parse_memos_by_type_pure(memos)
        assert "friendly" in result["PersonalityNotes"].lower()
        assert "playful" in result["PersonalityNotes"].lower()
        assert "temperament" in result["PersonalityNotes"].lower()

    def test_medical_keywords(self):
        """Test categorization of medical-related notes."""
        from scraper.parsers import parse_memos_by_type_pure

        memos = """
        <p>2024-01-20</p>
        <p>Medical exam shows heart condition. Started medication for treatment.</p>
        <p>2024-01-25</p>
        <p>Vaccine administered, no adverse reaction.</p>
        """
        result = parse_memos_by_type_pure(memos)
        assert "medical" in result["MedicalNotes"].lower()
        assert "medication" in result["MedicalNotes"].lower()
        assert "vaccine" in result["MedicalNotes"].lower()

    def test_intake_keywords(self):
        """Test categorization of intake-related notes."""
        from scraper.parsers import parse_memos_by_type_pure

        memos = """
        <p>Intake notes: Dog came from owner surrender. Background: previous owner had health issues.</p>
        """
        result = parse_memos_by_type_pure(memos)
        assert "intake" in result["IntakeNotes"].lower()
        assert "owner surrender" in result["IntakeNotes"].lower()
        assert "background" in result["IntakeNotes"].lower()

    def test_mixed_categories(self):
        """Test that notes are correctly separated into categories."""
        from scraper.parsers import parse_memos_by_type_pure

        memos = """
        <p>2024-01-10</p>
        <p>Intake: Dog rescued from shelter. Previous history unknown.</p>

        <p>2024-01-15</p>
        <p>Medical: Health check completed. Started heartworm treatment.</p>

        <p>2024-01-20</p>
        <p>Behavior: Very friendly and social. Good temperament with children.</p>
        """
        result = parse_memos_by_type_pure(memos)

        # Each category should have its relevant content
        assert (
            "intake" in result["IntakeNotes"].lower() or "rescued" in result["IntakeNotes"].lower()
        )
        assert (
            "medical" in result["MedicalNotes"].lower()
            or "treatment" in result["MedicalNotes"].lower()
        )
        assert (
            "friendly" in result["PersonalityNotes"].lower()
            or "temperament" in result["PersonalityNotes"].lower()
        )

    def test_html_tag_stripping(self):
        """Test that HTML tags are properly removed."""
        from scraper.parsers import parse_memos_by_type_pure

        memos = "<p><strong>Personality:</strong> Very <em>friendly</em> dog.</p><br/><p>Medical: Needs <b>medication</b>.</p>"
        result = parse_memos_by_type_pure(memos)

        # Should not contain HTML tags
        assert "<p>" not in result["PersonalityNotes"]
        assert "<strong>" not in result["PersonalityNotes"]
        assert "<em>" not in result["PersonalityNotes"]
        assert "<b>" not in result["MedicalNotes"]

    def test_priority_order_medical_over_intake(self):
        """Test that medical keywords take priority when multiple categories match."""
        from scraper.parsers import parse_memos_by_type_pure

        memos = """
        <p>Intake medical exam shows dog is healthy. Previous medical history unavailable.</p>
        """
        result = parse_memos_by_type_pure(memos)

        # Should be categorized as medical (higher priority)
        assert "medical" in result["MedicalNotes"].lower()
        # Intake should be empty or minimal since medical took priority
        assert len(result["MedicalNotes"]) > len(result["IntakeNotes"])

    def test_short_sections_ignored(self):
        """Test that very short sections are filtered out."""
        from scraper.parsers import parse_memos_by_type_pure

        memos = """
        <p>OK</p>
        <p>This is a longer section about the dog's friendly personality and calm behavior.</p>
        <p>.</p>
        """
        result = parse_memos_by_type_pure(memos)

        # Should only include the longer meaningful section
        assert "friendly" in result["PersonalityNotes"].lower()
        assert result["PersonalityNotes"].count("\n") < 3  # Not many sections

    def test_memo_parsing_helper_functions(self, parser):
        """Test individual helper functions for memo parsing."""

        # Test HTML cleaning
        html = "<p>Hello <strong>world</strong></p><br/>Test"
        clean = parser._clean_memo_html(html)
        assert "<p>" not in clean
        assert "<strong>" not in clean
        assert "<br" not in clean
        assert "Hello" in clean and "world" in clean  # Content is preserved
        assert "Test" in clean

        # Test section splitting (raw split may include empty strings)
        text = "2024-01-15\n\nFirst section\n\n2024-01-20\n\nSecond section"
        sections = parser._split_memo_into_sections(text)
        # Filter out empty sections like the main parsing logic does
        non_empty_sections = [s for s in sections if s.strip()]
        assert len(non_empty_sections) == 2
        assert "First section" in non_empty_sections[0]
        assert "Second section" in non_empty_sections[1]

        # Test keyword counting
        keywords = ["dog", "cat", "bird"]
        assert parser._count_keywords("The dog is friendly", keywords) == 1
        assert parser._count_keywords("The dog and cat are friendly", keywords) == 2
        assert parser._count_keywords("The fish is friendly", keywords) == 0

        # Test categorization
        assert parser._categorize_memo_section("medical exam required") == "medical"
        assert parser._categorize_memo_section("intake from shelter") == "intake"
        assert parser._categorize_memo_section("friendly personality") == "personality"
        assert parser._categorize_memo_section("random text") == ""

        # Test keyword getters
        personality_keywords = parser._get_personality_keywords()
        assert "friendly" in personality_keywords
        assert "playful" in personality_keywords

        intake_keywords = parser._get_intake_keywords()
        assert "intake" in intake_keywords
        assert "background" in intake_keywords

        medical_keywords = parser._get_medical_keywords()
        assert "medical" in medical_keywords
        assert "vaccine" in medical_keywords
