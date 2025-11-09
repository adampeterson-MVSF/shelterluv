#!/usr/bin/env python3
# Do not deploy this; local tooling only

"""
Source Code Collector - LLM-Optimized
Python implementation of source code collection tool.

For local code-bundling only; not part of deployment.
Run with: python dev_tools/source_collector.py
"""

# Simple launcher that imports from the modular app
from dev_tools.source_collector.app import app

if __name__ == '__main__':
    print("Source Code Collector - Python Version")
    print("Starting web server on http://localhost:5000")
    print("Open your browser and navigate to the URL above")
    app.run(debug=True, host='0.0.0.0', port=5000)
