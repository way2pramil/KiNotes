"""
KiNotes Version Information

Single source of truth for version across the project.
Automatically parsed from metadata.json during build/distribution.
"""

import os
import json

__version__ = "1.5.0"
__author__ = "PCBtools.xyz"
__license__ = "Apache-2.0"

def get_version():
    """Get version from metadata.json or fallback to hardcoded."""
    try:
        metadata_path = os.path.join(os.path.dirname(__file__), "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                data = json.load(f)
                if "versions" in data and len(data["versions"]) > 0:
                    return data["versions"][0].get("version", __version__)
    except:
        pass
    return __version__

# Set version from metadata
__version__ = get_version()
