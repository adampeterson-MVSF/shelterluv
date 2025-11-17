#!/usr/bin/env python3
"""
Check if ShelterLuv credentials are properly configured.

Run this script to verify your credentials are accessible:
    python check_credentials.py
"""

from config import EtlConfig
from errors import EtlError
from secret_manager import get_shelterluv_creds


def check_credentials():
    """Check if all required credentials are accessible."""
    print("🔍 Checking ShelterLuv credentials...")
    print("=" * 50)

    try:
        # Create ETL config (which includes secrets config) and test access
        config = EtlConfig.from_env()
        creds = get_shelterluv_creds(config.secrets)

        # Display results
        print(f"✅ Secrets mode: {config.secrets.mode.value}")
        print(f"✅ Project ID: {config.secrets.project_id}")
        print(f"✅ SHELTERLUV_USER: {creds['username']}")
        print("✅ SHELTERLUV_PASS: [HIDDEN]")
        print(f"✅ SHELTERLUV_API_KEY: {creds['api_key'][:10]}...")

        print("=" * 50)
        print("🎉 All credentials are configured correctly!")
        print("\nNext steps:")
        print("1. Run: python run_etl_local.py --limit 5")
        print("2. Or: python run_etl_local.py  (for full run)")

        return True

    except EtlError as e:
        print(f"❌ Credential check failed: {e}")
        print("=" * 50)
        print("❌ Missing or invalid credentials!")
        print("\nTo fix:")

        if "DISABLE_SECRET_MANAGER" in str(e) or "env" in str(e).lower():
            print("1. Create file: services/etl_scraper_py/.env.local")
            print("2. Add these lines:")
            print("   SHELTERLUV_USER=your_username")
            print("   SHELTERLUV_PASS=your_password")
            print("   SHELTERLUV_API_KEY=your_api_key")
            print("3. Restart your terminal")
        else:
            print("1. Ensure you're authenticated with Google Cloud:")
            print("   gcloud auth application-default login")
            print("2. Or set DISABLE_SECRET_MANAGER=1 to use environment variables")

        print("4. Run this script again to verify")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("=" * 50)
        print("❌ Credential configuration error!")
        return False


if __name__ == "__main__":
    check_credentials()
