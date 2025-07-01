import json
import os
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Utility for loading configuration and whitelists."""
    
    @staticmethod
    def load_whitelist(resource_type: str, custom_path: Optional[str] = None) -> List[str]:
        """
        Load whitelist for a specific resource type.
        
        Args:
            resource_type: Type of resource (e.g., 'model_endpoints', 'apps')
            custom_path: Optional custom path to whitelist file
            
        Returns:
            List of whitelisted resource IDs
            
        Raises:
            FileNotFoundError: If whitelist file doesn't exist
            json.JSONDecodeError: If whitelist file is invalid JSON
        """
        if custom_path:
            whitelist_path = custom_path
        else:
            # Default path relative to the job's working directory
            whitelist_path = f"/Workspace/config/whitelists/{resource_type}.json"
            
            # For local development, use relative path
            if not os.path.exists(whitelist_path):
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                whitelist_path = os.path.join(project_root, "config", "whitelists", f"{resource_type}.json")
        
        logger.info(f"Loading whitelist from: {whitelist_path}")
        
        try:
            with open(whitelist_path, 'r') as f:
                data = json.load(f)
                
            # Support both array format and object with 'whitelist' key
            if isinstance(data, list):
                whitelist = data
            elif isinstance(data, dict) and 'whitelist' in data:
                whitelist = data['whitelist']
            else:
                raise ValueError("Invalid whitelist format. Expected array or object with 'whitelist' key")
            
            logger.info(f"Loaded {len(whitelist)} whitelisted IDs for {resource_type}")
            return whitelist
            
        except FileNotFoundError:
            logger.error(f"Whitelist file not found: {whitelist_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in whitelist file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading whitelist: {e}")
            raise
    
    @staticmethod
    def create_default_whitelist(resource_type: str, resource_ids: List[str]) -> str:
        """
        Create a default whitelist file for a resource type.
        
        Args:
            resource_type: Type of resource
            resource_ids: List of resource IDs to whitelist
            
        Returns:
            Path to created whitelist file
        """
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        whitelist_dir = os.path.join(project_root, "config", "whitelists")
        os.makedirs(whitelist_dir, exist_ok=True)
        
        whitelist_path = os.path.join(whitelist_dir, f"{resource_type}.json")
        
        whitelist_data = {
            "description": f"Whitelist for {resource_type}",
            "whitelist": resource_ids
        }
        
        with open(whitelist_path, 'w') as f:
            json.dump(whitelist_data, f, indent=2)
        
        logger.info(f"Created default whitelist at: {whitelist_path}")
        return whitelist_path