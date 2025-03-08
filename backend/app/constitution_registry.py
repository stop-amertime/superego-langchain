import os
import glob
import logging
from typing import Dict, List, Any, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConstitutionRegistry:
    """Registry for managing constitutions from individual files"""
    
    def __init__(self, directory: str):
        self.directory = directory
        self.constitutions = {}
        self._load_constitutions()
    
    def _load_constitutions(self):
        """Load all constitutions from the directory"""
        # Create directory if it doesn't exist
        os.makedirs(self.directory, exist_ok=True)
        
        # Load constitutions from markdown files
        for file_path in glob.glob(os.path.join(self.directory, "*.md")):
            try:
                constitution_id = os.path.basename(file_path).replace(".md", "")
                name, content = self._parse_constitution_file(file_path)
                self.constitutions[constitution_id] = {
                    "id": constitution_id,
                    "name": name,
                    "content": content
                }
                logger.info(f"Loaded constitution: {name} (ID: {constitution_id})")
            except Exception as e:
                logger.error(f"Error loading constitution from {file_path}: {e}")
    
    def _parse_constitution_file(self, file_path: str) -> Tuple[str, str]:
        """Parse a constitution file to extract name and content"""
        with open(file_path, 'r') as f:
            content = f.read()
            lines = content.split('\n')
            
            # Extract name from first line if it's a markdown heading
            if lines and lines[0].startswith('# '):
                name = lines[0][2:].strip()
                content = '\n'.join(lines[1:]).strip()
                return name, content
            
            # Default name if no heading found
            return os.path.basename(file_path).replace(".md", ""), content
    
    def get_constitution(self, constitution_id: str) -> Optional[Dict[str, Any]]:
        """Get a constitution by ID"""
        return self.constitutions.get(constitution_id)
    
    def get_all_constitutions(self) -> Dict[str, Dict[str, Any]]:
        """Get all constitutions"""
        return self.constitutions
    
    def save_constitution(self, constitution_id: str, name: str, content: str) -> bool:
        """Save a constitution to a file"""
        file_path = os.path.join(self.directory, f"{constitution_id}.md")
        try:
            with open(file_path, 'w') as f:
                f.write(f"# {name}\n\n{content}")
            
            # Update in-memory cache
            self.constitutions[constitution_id] = {
                "id": constitution_id,
                "name": name,
                "content": content
            }
            logger.info(f"Saved constitution: {name} (ID: {constitution_id})")
            return True
        except Exception as e:
            logger.error(f"Error saving constitution: {e}")
            return False
