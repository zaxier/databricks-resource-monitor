from typing import List, Dict, Any
from .base import ResourceHandler
import logging

logger = logging.getLogger(__name__)


class AppsHandler(ResourceHandler):
    """Handler for Databricks Apps."""
    
    def list_resources(self) -> List[Dict[str, Any]]:
        """List all Databricks apps in the workspace."""
        try:
            apps = list(self.client.apps.list())
            resources = []
            
            for app in apps:
                resources.append({
                    'id': app.name,
                    'name': app.name,
                    'state': app.status.state if hasattr(app, 'status') and hasattr(app.status, 'state') else 'UNKNOWN',
                    'creator': app.creator if hasattr(app, 'creator') else 'UNKNOWN',
                    'creation_time': app.create_time if hasattr(app, 'create_time') else None,
                    'raw': app
                })
            
            logger.info(f"Found {len(resources)} Databricks apps")
            return resources
            
        except Exception as e:
            logger.error(f"Error listing Databricks apps: {str(e)}")
            raise
    
    def delete_resource(self, resource_id: str) -> bool:
        """Delete a Databricks app."""
        try:
            self.client.apps.delete(app_name=resource_id)
            logger.info(f"Successfully deleted Databricks app: {resource_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete Databricks app {resource_id}: {str(e)}")
            return False
    
    def get_resource_id(self, resource: Dict[str, Any]) -> str:
        """Extract the app name as ID."""
        return resource['id']
    
    def get_resource_details(self, resource: Dict[str, Any]) -> str:
        """Get human-readable details about the app."""
        details = [
            f"Name: {resource['name']}",
            f"State: {resource['state']}",
            f"Creator: {resource['creator']}",
        ]
        
        if resource['creation_time']:
            details.append(f"Created: {resource['creation_time']}")
        
        return " | ".join(details)