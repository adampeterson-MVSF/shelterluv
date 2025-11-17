#!/usr/bin/env python3
"""
Test script to check what the scraper extracts for a single dog.
Shows the raw scraped data vs what gets stored.
"""

import os
import json
from config import EtlConfig
from extract import extract, ExtractConfig

def test_single_scrape(target_internal_id=None):
    """Test scraping a single dog and show what data is extracted."""

    # Force environment mode for secrets
    os.environ['DISABLE_SECRET_MANAGER'] = '1'
    os.environ['ENV_PROFILE'] = 'main'

    # Get configuration
    config = EtlConfig.from_env()

    # Get credentials
    from secret_manager import get_shelterluv_creds
    creds = get_shelterluv_creds(config.secrets)

    # Run extraction phase to get data for one dog
    print("Running extraction phase...")
    extract_config = ExtractConfig(
        memos_mode=config.memos_mode,
        max_concurrent_scrapes=config.max_concurrent_scrapes,
        dry_run=config.dry_run,
        animal_limit=1,  # Just one dog
        skip_events_people=config.skip_events_people
    )

    extract_result = extract(creds, extract_config)

    if not extract_result.animals_by_id:
        print("No animals found!")
        return

    # Get the first animal, or find the target animal
    if target_internal_id:
        if target_internal_id in extract_result.animals_by_id:
            internal_id = target_internal_id
            animal_data = extract_result.animals_by_id[internal_id]
        else:
            print(f"Target animal {target_internal_id} not found in current extraction. Available animals:")
            for iid, adata in extract_result.animals_by_id.items():
                print(f"  {iid}: {adata.get('Name')} ({adata.get('ID')})")
            return
    else:
        # Get the first animal
        internal_id, animal_data = next(iter(extract_result.animals_by_id.items()))

    animal_id = animal_data.get('ID')
    print(f"Testing on dog: {animal_data.get('Name')} (ID: {animal_id}, Internal-ID: {internal_id})")

    # Get scraped data for this animal
    scraped_data = extract_result.scraped_map.get(str(internal_id), {})
    print(f"Scraped data has {len(scraped_data)} fields")

    # Show API data
    print("\n=== API DATA ===")
    api_fields = ['Breed', 'Color', 'Pattern', 'DistinguishingMarks', 'AgeGroup', 'EstBirthdate', 'Location', 'Stage']
    for field in api_fields:
        value = animal_data.get(field)
        print(f"{field}: {repr(value)}")

    # Show scraped data
    print("\n=== SCRAPED DATA ===")
    scraped_fields = ['Species', 'Color', 'Pattern', 'DistinguishingMarks', 'AdoptionPrice', 'MicrochipNumber', 'MicrochipIssuer', 'MicrochipImplantDate', 'AlteredBeforeArrival', 'AlteredInCare', 'AgeGroup', 'EstBirthdate', 'Photos', 'CaseManager', 'MemosRawHTML', 'PersonalityNotes', 'IntakeNotes', 'MedicalNotes']
    for field in scraped_fields:
        value = scraped_data.get(field)
        if field == 'Photos':
            print(f"{field}: {len(value) if isinstance(value, list) else 0} images")
            if isinstance(value, list) and value:
                for i, url in enumerate(value[:3]):  # Show first 3 URLs
                    print(f"  {i+1}: {url}")
                if len(value) > 3:
                    print(f"  ... and {len(value)-3} more")
        elif field == 'MemosRawHTML':
            memos_content = value or ""
            print(f"{field}: {len(memos_content)} characters")
            if memos_content:
                # Show first 500 chars
                preview = memos_content[:500].replace('\n', '\\n')
                print(f"  Preview: {preview}{'...' if len(memos_content) > 500 else ''}")
            else:
                print("  (empty)")
        elif field in ['PersonalityNotes', 'IntakeNotes', 'MedicalNotes']:
            notes_content = value or ""
            print(f"{field}: {len(notes_content)} characters")
            if notes_content:
                preview = notes_content[:200].replace('\n', '\\n')
                print(f"  Preview: {preview}{'...' if len(notes_content) > 200 else ''}")
            else:
                print("  (empty)")
        else:
            print(f"{field}: {repr(value)}")

    # Show what would be stored after enrichment
    from enrichment import build_dog_record

    try:
        final_dog = build_dog_record(animal_data, scraped_data, {}, {}, "")

        print("\n=== FINAL STORED DATA (after enrichment) ===")
        stored_fields = ['Breed', 'Color', 'Pattern', 'DistinguishingMarks', 'AgeGroup', 'EstBirthdate', 'Location', 'Stage', 'Species', 'AdoptionPrice', 'MicrochipNumber', 'MicrochipIssuer', 'MicrochipImplantDate', 'AlteredBeforeArrival', 'AlteredInCare', 'Photos']
        for field in stored_fields:
            value = final_dog.get(field)
            if field == 'Photos':
                has_value = isinstance(value, list) and len(value) > 0
                print(f"{field}: {len(value) if isinstance(value, list) else 0} images {'✓' if has_value else '✗'}")
            else:
                has_value = value is not None and value != ''
                print(f"{field}: {repr(value)} {'✓' if has_value else '✗'}")

    except Exception as e:
        print(f"Error building dog record: {e}")

if __name__ == "__main__":
    import sys
    target_id = sys.argv[1] if len(sys.argv) > 1 else None
    test_single_scrape(target_id)
