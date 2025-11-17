#!/usr/bin/env python3
"""
Generate Python type definitions from the canonical dog schema.
Creates services/etl-scraper-py/dog_types.py with typed dataclasses.

This script now delegates to the unified schema artifacts pipeline
instead of reimplementing schema parsing logic.

Usage:
    python3 scripts/generate_python_dog_types.py
"""

import subprocess
import sys
import os


def generate_python_types():
    """Generate Python types using the unified schema artifacts pipeline."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # Change to project root so relative paths work
    os.chdir(project_root)

    try:
        # Call the Node.js schema artifacts CLI to generate all artifacts (including Python types)
        result = subprocess.run([
            'node', 'schemaArtifactsCli.js'
        ], capture_output=True, text=True, check=True)

        print("✅ Python dog types generated successfully")
        print(result.stdout)

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate Python types: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)


if __name__ == '__main__':
    generate_python_types()
