"""
Cloud Function entry point for ETL pipeline.

This module provides the HTTP endpoint for triggering ETL runs in production.
It is NOT a CLI entry point - use run_etl_local.py or other CLI scripts for local development.
"""

import logging
import os
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

import functions_framework

import pipeline
from config import EtlConfig
from errors import EtlError
from secret_manager import get_shelterluv_creds

logger = logging.getLogger(__name__)


def check_auth(request) -> bool:
    """Check for valid authentication token."""
    # Check for shared secret in header or query param
    auth_header = request.headers.get("X-ShelterLuv-Token")
    auth_param = request.args.get("token")

    expected_token = os.environ.get("SHELTERLUV_ETL_TOKEN")
    if not expected_token:
        return False

    return (auth_header == expected_token) or (auth_param == expected_token)


@functions_framework.http
def run_shelterluv_etl(request) -> Tuple[Dict[str, Any], int]:
    """
    Cloud Function entry – do NOT add business logic here.
    """

    # Basic environment validation: we only care about the ETL auth token here.
    etl_token = os.environ.get("SHELTERLUV_ETL_TOKEN")
    if not etl_token:
        logger.error("Environment configuration error: Missing SHELTERLUV_ETL_TOKEN")
        return {"status": "error", "message": "Server configuration error"}, 500

    # Check authentication
    if not check_auth(request):
        return {"status": "error", "message": "Unauthorized"}, 401

    run_id = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    try:
        # Create production config for Cloud Function
        config = EtlConfig.from_env(overrides={"env_profile": "prod"})

        # Get credentials using config
        creds = get_shelterluv_creds(config.secrets)

        stats = pipeline.run_etl_process(config, creds)
        return {"status": "ok", "run_id": run_id, "stats": stats}, 200
    except EtlError as e:
        logger.error(f"ETL run {run_id} failed: {e}")
        return {"status": "error", "run_id": run_id, "message": str(e)}, 500
    except Exception as e:
        logger.error(f"ETL run {run_id} failed with unexpected error: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return {"status": "error", "run_id": run_id, "message": "Internal server error"}, 500
