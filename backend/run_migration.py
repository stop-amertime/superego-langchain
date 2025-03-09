#!/usr/bin/env python3
"""
Script to run the migration from the old format to the new format.

This script will:
1. Load existing flow templates and create flow definitions
2. Load existing flow instances and update them to the new format
3. Load messages from the message store and add them to flow instances
"""

import os
import sys
import logging

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the migration."""
    logger.info("Starting migration...")
    
    try:
        # Import the migration module
        from app.migrate_flow_data import migrate_data
        
        # Run the migration
        migrate_data()
        
        logger.info("Migration completed successfully")
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
