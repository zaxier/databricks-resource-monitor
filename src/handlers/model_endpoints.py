from typing import List, Dict, Any
from .base import ResourceHandler
import logging

logger = logging.getLogger(__name__)


class ModelEndpointHandler(ResourceHandler):
    """Handler for Databricks Model Serving Endpoints."""
    
    def list_resources(self) -> List[Dict[str, Any]]:
        """List all model serving endpoints in the workspace."""
        try:
            endpoints = list(self.client.serving_endpoints.list())
            resources = []
            
            for endpoint in endpoints:
                resources.append({
                    'id': endpoint.name,  # Using name as ID for endpoints
                    'name': endpoint.name,
                    'state': endpoint.state.config_update if hasattr(endpoint.state, 'config_update') else 'UNKNOWN',
                    'creator': endpoint.creator if hasattr(endpoint, 'creator') else 'UNKNOWN',
                    'creation_timestamp': endpoint.creation_timestamp if hasattr(endpoint, 'creation_timestamp') else None,
                    'raw': endpoint
                })
            
            logger.info(f"Found {len(resources)} model serving endpoints")
            return resources
            
        except Exception as e:
            logger.error(f"Error listing model serving endpoints: {str(e)}")
            raise
    
    def delete_resource(self, resource_id: str) -> bool:
        """Delete a model serving endpoint."""
        try:
            self.client.serving_endpoints.delete(name=resource_id)
            logger.info(f"Successfully deleted model serving endpoint: {resource_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete model serving endpoint {resource_id}: {str(e)}")
            return False
    
    def get_resource_id(self, resource: Dict[str, Any]) -> str:
        """Extract the endpoint name as ID."""
        return resource['id']
    
    def get_resource_details(self, resource: Dict[str, Any]) -> str:
        """Get human-readable details about the endpoint."""
        details = [
            f"Name: {resource['name']}",
            f"State: {resource['state']}",
            f"Creator: {resource['creator']}",
        ]
        
        if resource['creation_timestamp']:
            details.append(f"Created: {resource['creation_timestamp']}")
        
        return " | ".join(details)