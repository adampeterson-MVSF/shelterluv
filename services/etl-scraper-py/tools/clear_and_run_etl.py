#!/usr/bin/env python3
"""
🚨 EXTREME DANGER: DATABASE DESTRUCTION SCRIPT 🚨
🚨 DEVELOPMENT/TESTING ONLY - NEVER RUN IN PRODUCTION 🚨

This script PERMANENTLY DELETES ALL DOG RECORDS from the Firestore database
and replaces them with a fresh ETL run.

*** THIS IS IRREVERSIBLE - NO BACKUP IS MADE ***
*** PRODUCTION DATA WILL BE LOST FOREVER ***

ONLY USE IN DEVELOPMENT/TESTING ENVIRONMENTS WITH TEST DATA.

For production: Use normal ETL process (run_etl_local.py) which only updates changed records.

Requirements:
1. Must be run with --i-understand-this-will-destroy-all-dog-data
2. Must be in a development/test project (not production)
3. Must confirm by typing the project name

Usage: python clear_and_run_etl.py --i-understand-this-will-destroy-all-dog-data
"""

import logging
import sys
import os
import pipeline
import db
from errors import EtlError
from common import guard_dev_only

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_info():
    """Get project information for safety checks."""
    project_id = os.environ.get("GCP_PROJECT", os.environ.get("FIREBASE_PROJECT_ID", "muttville"))
    return project_id

def confirm_destruction(project_id):
    """Get explicit user confirmation for destructive operation."""
    print("\n" + "🚨" * 60)
    print("🚨 EXTREME DANGER ZONE - DATABASE DESTRUCTION CONFIRMATION 🚨")
    print("🚨" * 60)
    print()
    print("You are about to PERMANENTLY DELETE ALL DOG RECORDS from:")
    print(f"   Project: {project_id}")
    print("   Collection: dogs")
    print()
    print("This action:")
    print("   ❌ CANNOT BE UNDONE")
    print("   ❌ HAS NO BACKUP")
    print("   ❌ WILL DELETE ALL DOG PHOTOS, MEDICAL RECORDS, FOSTER INFO")
    print()
    print("Type the exact project name to confirm destruction:")
    print(f"   Expected: '{project_id}'")
    print()

    try:
        confirmation = input("Confirm by typing project name: ").strip()
        if confirmation != project_id:
            print(f"❌ Confirmation failed. Expected '{project_id}', got '{confirmation}'")
            return False
        return True
    except (EOFError, KeyboardInterrupt):
        print("\n❌ Operation cancelled by user")
        return False

def main():
    """Clear database and run ETL process with extreme guardrails."""
    # EXTREME SAFETY CHECK 1: Require explicit destructive flag
    dangerous_flag = "--i-understand-this-will-destroy-all-dog-data"
    if dangerous_flag not in sys.argv:
        print("\n" + "🚨" * 80)
        print("🚨 DATABASE DESTRUCTION SCRIPT - SAFETY CHECK FAILED 🚨")
        print("🚨" * 80)
        print()
        print("This script will PERMANENTLY DELETE ALL DOG DATA from Firestore.")
        print("Production data loss is IRREVERSIBLE.")
        print()
        print("To run this script, you must include this exact flag:")
        print(f"   {dangerous_flag}")
        print()
        print("And then you'll need to type the project name to confirm.")
        print()
        print("For normal ETL updates (safe, only changes modified records):")
        print("   python run_etl_local.py")
        return 1

    # EXTREME SAFETY CHECK 2: Refuse to run against production project IDs
    guard_dev_only()
    project_id = get_project_info()
    print(f"✅ Project safety check passed: {project_id}")

    # EXTREME SAFETY CHECK 3: User must type project name to confirm
    if not confirm_destruction(project_id):
        print("\n❌ Database destruction cancelled.")
        return 1

    print("\n" + "💀" * 60)
    print("💀 FINAL WARNING: DESTRUCTION IMMINENT 💀")
    print("💀" * 60)
    print()
    print("🚨 ABOUT TO DELETE ALL DOG DATA FROM FIRESTORE 🚨")
    print(f"   Project: {project_id}")
    print("   Collection: dogs")
    print()
    print("This will permanently remove:")
    print("   • All dog profiles and photos")
    print("   • All medical records and treatment history")
    print("   • All foster parent contact information")
    print("   • All adoption and event tracking data")
    print()
    print("⚠️  Press Ctrl+C NOW if you changed your mind!")
    print()

    # Give user one final chance to cancel
    import time
    for i in range(5, 0, -1):
        print(f"Starting destruction in {i} seconds... (Ctrl+C to cancel)")
        time.sleep(1)

    logger.info("=" * 80)
    logger.info("💀 DESTRUCTION COMMENCING - NO TURNING BACK NOW 💀")
    logger.info("=" * 80)

    try:
        # Step 1: Clear all dogs from database
        logger.info("🗑️  Clearing ALL dogs from database...")
        logger.info("   This operation cannot be undone!")
        cleared_count = db.clear_all_dogs()
        logger.info(f"✅ DESTROYED {cleared_count} dog records from database")

        # Step 2: Run ETL pipeline
        logger.info("🔄 Running ETL pipeline...")
        stats = pipeline.run_etl_process()

        print("\n" + "🎉" * 60)
        print("🎉 DATABASE DESTRUCTION AND RECREATION COMPLETED 🎉")
        print("🎉" * 60)
        print()
        print("💀 DESTRUCTION SUMMARY:")
        print(f"   Records destroyed: {cleared_count}")
        print()
        print("🔄 RECREATION SUMMARY:")
        print(f"   Animals fetched: {stats['total_animals_fetched']}")
        print(f"   Events fetched: {stats['total_events_fetched']}")
        print(f"   People fetched: {stats['total_people_fetched']}")
        print(f"   Dogs processed: {stats['dogs_processed']}")
        print(f"   Invalid dogs: {stats['dogs_invalid']}")
        print(f"   Dogs written: {stats['dogs_written']}")
        print(f"   Dogs with foster: {stats['dogs_with_foster']}")
        if stats.get('events_fetch_failed'):
            print("   ⚠️  Events fetch failed")
        if stats.get('people_fetch_failed'):
            print("   ⚠️  People fetch failed")
        if stats.get('partial_data'):
            print("   ⚠️  Partial data - some enrichment may be missing")
        print()
        print("✅ Database has been completely replaced with fresh ETL data.")
        print("✅ All previous dog records have been permanently deleted.")
        print("=" * 60)

        return 0

    except EtlError as e:
        logger.error("=" * 80)
        logger.error(f"ETL FAILED: {e}")
        logger.error("=" * 80)
        return 1

    except Exception as e:
        logger.exception("=" * 80)
        logger.exception(f"UNEXPECTED ERROR: {e}")
        logger.exception("=" * 80)
        return 1

if __name__ == "__main__":
    exit(main())
