#!/usr/bin/env python
"""
Script to migrate constitutions from JSON to individual markdown files.
"""
import os
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONSTITUTIONS_FILE = os.path.join(SCRIPT_DIR, "data", "constitutions.json")
CONSTITUTIONS_DIR = os.path.join(SCRIPT_DIR, "data", "constitutions")

def migrate_constitutions():
    """Migrate constitutions from JSON to individual files"""
    try:
        # Load from JSON
        with open(CONSTITUTIONS_FILE, 'r') as f:
            data = json.load(f)
            constitutions = data.get("constitutions", [])
        
        # Create directory if it doesn't exist
        os.makedirs(CONSTITUTIONS_DIR, exist_ok=True)
        
        # Save each constitution to a file
        for constitution in constitutions:
            constitution_id = constitution["id"]
            name = constitution["name"]
            content = constitution["content"]
            
            file_path = os.path.join(CONSTITUTIONS_DIR, f"{constitution_id}.md")
            with open(file_path, 'w') as f:
                f.write(f"# {name}\n\n{content}")
            
            logger.info(f"Migrated constitution: {name} (ID: {constitution_id})")
        
        logger.info(f"Migration complete. {len(constitutions)} constitutions migrated.")
        return True
    except Exception as e:
        logger.error(f"Error migrating constitutions: {e}")
        return False

if __name__ == "__main__":
    migrate_constitutions()
