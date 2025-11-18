#!/usr/bin/env python3
"""
Compare ETL API data vs UI scraping to detect divergences.

This script:
1. Runs ETL pipeline to get canonical API data
2. Scrapes ShelterLuv UI to get what users actually see
3. Compares the datasets and reports any differences
4. Useful for detecting ShelterLuv UI/API changes that break ETL

Usage:
    python compare_etl_vs_ui.py [--dry-run]
"""

import logging
import os
import sys
from typing import Any, Dict, List, Set

from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")
load_dotenv(".env.local")

from project_safety import guard_dev_only
from config import EtlConfig

# Set the Google Cloud project using config system
config = EtlConfig.from_env()
os.environ["GOOGLE_CLOUD_PROJECT"] = config.project_id

from scrape_ui_dogs import get_ui_animal_ids, scrape_animals_from_ui

# Import our modules after setting environment
from pipeline import run_etl_process
from secret_manager import get_shelterluv_creds

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def compare_etl_vs_ui(dry_run: bool = False) -> Dict[str, Any]:
    """
    Compare ETL API data against UI scraping to detect divergences.

    Returns comparison results including:
    - ETL animal count vs UI animal count
    - Animals in ETL but not in UI
    - Animals in UI but not in ETL
    - Summary statistics
    """
    print("🔄 COMPARING ETL API DATA VS UI SCRAPING")
    print("=" * 80)

    # Safety check for development environment
    guard_dev_only()

    try:
        # PHASE 1: Run ETL to get canonical data
        print("\n🔍 PHASE 1: RUNNING ETL PIPELINE")
        config = EtlConfig.from_env(overrides={"dry_run": dry_run, "animal_limit": 50})
        creds = get_shelterluv_creds(config.secrets)
        etl_stats = run_etl_process(config, creds)

        if etl_stats.get("dogs_processed", 0) == 0:
            print("❌ ETL found no dogs to process")
            return {"error": "ETL found no dogs"}

        print("✅ ETL completed successfully")
        print(f"   Dogs processed: {etl_stats.get('dogs_processed', 0)}")
        print(f"   In-custody IDs: {etl_stats.get('num_in_custody_ids', 0)}")

        # For now, we'll simulate having ETL animal IDs
        # In a real implementation, we'd need to query Firestore or capture IDs during ETL
        etl_animal_ids: set[str] = set()
        print(f"   ETL animal IDs tracked: {len(etl_animal_ids)}")

        # PHASE 2: Scrape UI to get what users see
        print("\n🌐 PHASE 2: SCRAPING UI DATA")
        ui_data = scrape_animals_from_ui()

        if "error" in ui_data:
            print(f"❌ UI scraping failed: {ui_data['error']}")
            return {"error": f'UI scraping failed: {ui_data["error"]}'}

        ui_animal_ids = get_ui_animal_ids(ui_data)
        print("✅ UI scraping completed successfully")
        print(f"   UI animal IDs found: {len(ui_animal_ids)}")
        print(f"   UI animal links: {ui_data.get('link_count', 0)}")
        print(f"   UI table elements: {ui_data.get('animal_count', 0)}")

        # PHASE 3: Compare datasets
        print("\n📊 PHASE 3: COMPARING DATASETS")

        # Animals in ETL but not in UI
        etl_only = etl_animal_ids - ui_animal_ids

        # Animals in UI but not in ETL
        ui_only = ui_animal_ids - etl_animal_ids

        # Animals in both
        both = etl_animal_ids & ui_animal_ids

        comparison = {
            "etl_total": len(etl_animal_ids),
            "ui_total": len(ui_animal_ids),
            "both_count": len(both),
            "etl_only": list(etl_only),
            "ui_only": list(ui_only),
            "overlap_percentage": (len(both) / max(len(etl_animal_ids | ui_animal_ids), 1)) * 100,
            "etl_stats": etl_stats,
            "ui_data": {
                "animal_count": ui_data.get("animal_count", 0),
                "link_count": ui_data.get("link_count", 0),
                "page_title": ui_data.get("page_title", ""),
                "url": ui_data.get("url", ""),
            },
        }

        return comparison

    except Exception as e:
        logger.exception(f"❌ Comparison failed: {e}")
        return {"error": str(e)}


def display_comparison_results(results: Dict[str, Any]):
    """Display comparison results in a readable format."""
    print("\n" + "=" * 80)
    print("📊 ETL vs UI COMPARISON RESULTS")
    print("=" * 80)

    if "error" in results:
        print(f"❌ ERROR: {results['error']}")
        return

    print("🐕 ETL DATA:")
    etl_stats = results.get("etl_stats", {})
    print(f"   Total dogs processed: {etl_stats.get('dogs_processed', 0)}")
    print(f"   In-custody IDs found: {etl_stats.get('num_in_custody_ids', 0)}")
    print(f"   ETL animal IDs tracked: {results.get('etl_total', 0)}")

    print("\n🌐 UI DATA:")
    ui_data = results.get("ui_data", {})
    print(f"   Page: {ui_data.get('page_title', 'Unknown')}")
    print(f"   URL: {ui_data.get('url', 'Unknown')}")
    print(f"   UI animal IDs found: {results.get('ui_total', 0)}")
    print(f"   UI table elements: {ui_data.get('animal_count', 0)}")
    print(f"   UI animal links: {ui_data.get('link_count', 0)}")

    print("\n🔄 COMPARISON:")
    print(f"   Animals in both ETL and UI: {results.get('both_count', 0)}")
    print(".1f")
    print(f"   Animals only in ETL: {len(results.get('etl_only', []))}")
    print(f"   Animals only in UI: {len(results.get('ui_only', []))}")

    # Show details of differences
    if results.get("etl_only"):
        print("\n🐕 ANIMALS IN ETL BUT NOT IN UI:")
        for animal_id in results["etl_only"][:10]:  # Show first 10
            print(f"   {animal_id}")
        if len(results["etl_only"]) > 10:
            print(f"   ... and {len(results['etl_only']) - 10} more")

    if results.get("ui_only"):
        print("\n🌐 ANIMALS IN UI BUT NOT IN ETL:")
        for animal_id in results["ui_only"][:10]:  # Show first 10
            print(f"   {animal_id}")
        if len(results["ui_only"]) > 10:
            print(f"   ... and {len(results['ui_only']) - 10} more")

    # Assessment
    overlap_pct = results.get("overlap_percentage", 0)
    if overlap_pct > 95:
        print("\n✅ ASSESSMENT: Excellent overlap (>95%) - ETL and UI are well synchronized")
    elif overlap_pct > 80:
        print("\n⚠️  ASSESSMENT: Good overlap (>80%) - Minor differences detected")
    else:
        print("\n❌ ASSESSMENT: Poor overlap (<80%) - Significant divergence detected!")
        print("   This may indicate ShelterLuv UI/API changes affecting ETL accuracy")

    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compare ETL API data vs UI scraping")
    parser.add_argument("--dry-run", action="store_true", help="Run ETL in dry-run mode")
    args = parser.parse_args()

    results = compare_etl_vs_ui(dry_run=args.dry_run)
    display_comparison_results(results)
