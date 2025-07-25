from typing import List
from databricks.sdk import WorkspaceClient
from ..handlers.base import ResourceHandler
from ..handlers.model_endpoints import ModelEndpointHandler
from ..handlers.apps import AppsHandler
from ..utils.config import ResourceConfig


class ResourceHandlerFactory:
    """Factory for creating appropriate resource handlers."""
    
    _handlers = {
        'model_endpoints': ModelEndpointHandler,
        'apps': AppsHandler,
    }
    
    @classmethod
    def create_handler(
        cls, 
        resource_type: str, 
        workspace_client: WorkspaceClient, 
        resource_config: ResourceConfig
    ) -> ResourceHandler:
        """
        Create a resource handler for the specified type.
        
        Args:
            resource_type: Type of resource ('model_endpoints', 'apps', etc.)
            workspace_client: Databricks workspace client
            resource_config: ResourceConfig with whitelist and filtering options
            
        Returns:
            Appropriate ResourceHandler instance
            
        Raises:
            ValueError: If resource_type is not supported
        """
        if resource_type not in cls._handlers:
            supported = ", ".join(cls._handlers.keys())
            raise ValueError(
                f"Unsupported resource type: {resource_type}. "
                f"Supported types: {supported}"
            )
        
        handler_class = cls._handlers[resource_type]
        return handler_class(workspace_client, resource_config)
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported resource types."""
        return list(cls._handlers.keys())