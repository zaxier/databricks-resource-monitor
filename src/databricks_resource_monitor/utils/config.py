import json
import os
from typing import List, Optional
import logging
import importlib.resources as pkg_resources
from databricks_resource_monitor.config import whitelists

logger = logging.getLogger(__name__)


class ResourceConfig:
    """Configuration for a resource type including whitelist and filtering options."""
    
    def __init__(self, whitelist: List[str], ignore_databricks_managed: bool = False):
        self.whitelist = whitelist
        self.ignore_databricks_managed = ignore_databricks_managed


class ConfigLoader:
    """Utility for loading configuration and whitelists."""
    
    @staticmethod
    def load_resource_config(resource_type: str, custom_path: Optional[str] = None) -> ResourceConfig:
        """
        Load configuration for a specific resource type.
        
        Args:
            resource_type: Type of resource (e.g., 'model_endpoints', 'apps')
            custom_path: Optional custom path to config file
            
        Returns:
            ResourceConfig with whitelist and filtering options
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        if custom_path:
            config_path = custom_path
            logger.info(f"Loading resource config from custom path: {config_path}")
            with open(config_path, 'r') as f:
                data = json.load(f)
        else:
            # First, try to load from package resources
            try:
                logger.info(f"Loading resource config from package for: {resource_type}")
                config_file = f"{resource_type}.json"
                config_data = pkg_resources.read_text(whitelists, config_file)
                data = json.loads(config_data)
                logger.info(f"Successfully loaded config from package")
            except (FileNotFoundError, ModuleNotFoundError) as e:
                logger.info(f"Package resource not found, trying workspace path")
                # Fallback to Databricks workspace path
                config_path = f"/Workspace/config/whitelists/{resource_type}.json"
                
                # For local development, use relative path
                if not os.path.exists(config_path):
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                    config_path = os.path.join(project_root, "config", "whitelists", f"{resource_type}.json")
                
                logger.info(f"Loading resource config from: {config_path}")
                with open(config_path, 'r') as f:
                    data = json.load(f)
        
        try:
            # Support both array format and object with 'whitelist' key
            if isinstance(data, list):
                whitelist = data
                ignore_databricks_managed = False
            elif isinstance(data, dict):
                if 'whitelist' in data:
                    whitelist = data['whitelist']
                else:
                    raise ValueError("Object format must contain 'whitelist' key")
                
                # Load filtering options
                ignore_databricks_managed = data.get('ignore_databricks_managed', False)
            else:
                raise ValueError("Invalid config format. Expected array or object with 'whitelist' key")
            
            logger.info(f"Loaded {len(whitelist)} whitelisted IDs for {resource_type}")
            if ignore_databricks_managed:
                logger.info(f"Configured to ignore Databricks-managed {resource_type}")
            
            return ResourceConfig(whitelist, ignore_databricks_managed)
            
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    @staticmethod
    def load_whitelist(resource_type: str, custom_path: Optional[str] = None) -> List[str]:
        """
        Load whitelist for a specific resource type (backward compatibility).
        
        Args:
            resource_type: Type of resource (e.g., 'model_endpoints', 'apps')
            custom_path: Optional custom path to whitelist file
            
        Returns:
            List of whitelisted resource IDs
        """
        config = ConfigLoader.load_resource_config(resource_type, custom_path)
        return config.whitelist
    
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
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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