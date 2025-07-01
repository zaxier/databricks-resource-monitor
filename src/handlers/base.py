from abc import ABC, abstractmethod
from typing import List, Dict, Any
from databricks.sdk import WorkspaceClient
import logging

logger = logging.getLogger(__name__)


class ResourceHandler(ABC):
    """Abstract base class for handling different Databricks resource types."""
    
    def __init__(self, workspace_client: WorkspaceClient, resource_config):
        """
        Initialize the resource handler.
        
        Args:
            workspace_client: Databricks workspace client
            resource_config: ResourceConfig with whitelist and filtering options
        """
        self.client = workspace_client
        self.whitelist = set(resource_config.whitelist)
        self.ignore_databricks_managed = resource_config.ignore_databricks_managed
        self.violations = []
    
    @abstractmethod
    def list_resources(self) -> List[Dict[str, Any]]:
        """
        List all resources of this type in the workspace.
        
        Returns:
            List of resource dictionaries with at least 'id' and 'name' fields
        """
        pass
    
    @abstractmethod
    def delete_resource(self, resource_id: str) -> bool:
        """
        Delete a specific resource.
        
        Args:
            resource_id: ID of the resource to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_resource_id(self, resource: Dict[str, Any]) -> str:
        """
        Extract the resource ID from a resource object.
        
        Args:
            resource: Resource dictionary
            
        Returns:
            Resource ID as string
        """
        pass
    
    @abstractmethod
    def get_resource_details(self, resource: Dict[str, Any]) -> str:
        """
        Get human-readable details about a resource for logging/alerting.
        
        Args:
            resource: Resource dictionary
            
        Returns:
            Formatted string with resource details
        """
        pass
    
    def is_databricks_managed(self, resource: Dict[str, Any]) -> bool:
        """
        Determine if a resource is managed by Databricks.
        
        Args:
            resource: Resource dictionary
            
        Returns:
            True if the resource appears to be Databricks-managed
        """
        # Check if creator is None and name starts with 'databricks-'
        creator = resource.get('creator')
        name = resource.get('name', '')
        
        return creator is None and name.startswith('databricks-')
    
    def check_resources(self, dry_run: bool = False) -> List[Dict[str, Any]]:
        """
        Check all resources against the whitelist and filtering rules.
        
        Args:
            dry_run: If True, only identify violations without taking action
            
        Returns:
            List of violation dictionaries
        """
        self.violations = []
        resources = self.list_resources()
        
        logger.info(f"Found {len(resources)} resources to check")
        
        for resource in resources:
            resource_id = self.get_resource_id(resource)
            
            # Skip if resource is in whitelist
            if resource_id in self.whitelist:
                continue
            
            # Skip if Databricks-managed and configured to ignore them
            if self.ignore_databricks_managed and self.is_databricks_managed(resource):
                logger.debug(f"Ignoring Databricks-managed resource: {resource_id}")
                continue
            
            # Resource is a violation
            violation = {
                'id': resource_id,
                'details': self.get_resource_details(resource),
                'action_taken': None
            }
            
            if not dry_run:
                logger.warning(f"Resource {resource_id} not in whitelist - marking for action")
            else:
                logger.info(f"[DRY RUN] Resource {resource_id} not in whitelist")
            
            self.violations.append(violation)
        
        logger.info(f"Found {len(self.violations)} violations")
        return self.violations
    
    def handle_violations(self, action_mode: str) -> Dict[str, Any]:
        """
        Handle violations based on the specified action mode.
        
        Args:
            action_mode: Either 'delete' or 'alert'
            
        Returns:
            Summary of actions taken
        """
        if not self.violations:
            logger.info("No violations to handle")
            return {'status': 'success', 'violations': 0, 'actions': []}
        
        results = {
            'status': 'success',
            'violations': len(self.violations),
            'actions': []
        }
        
        if action_mode == 'delete':
            for violation in self.violations:
                try:
                    success = self.delete_resource(violation['id'])
                    if success:
                        action = f"Deleted resource {violation['id']}"
                        violation['action_taken'] = 'deleted'
                    else:
                        action = f"Failed to delete resource {violation['id']}"
                        violation['action_taken'] = 'delete_failed'
                        results['status'] = 'partial_failure'
                    
                    results['actions'].append(action)
                    logger.info(action)
                    
                except Exception as e:
                    action = f"Error deleting resource {violation['id']}: {str(e)}"
                    violation['action_taken'] = 'error'
                    results['status'] = 'partial_failure'
                    results['actions'].append(action)
                    logger.error(action)
        
        elif action_mode == 'alert':
            # Generate alert by raising an exception that will trigger job failure
            # This will cause the configured email notifications to be sent
            violation_details = "\n".join([
                f"- {v['id']}: {v['details']}" 
                for v in self.violations
            ])
            
            error_message = (
                f"ALERT: Found {len(self.violations)} unauthorized resources:\n"
                f"{violation_details}\n\n"
                f"Please review and take appropriate action."
            )
            
            # This exception will cause the job to fail and trigger email notifications
            raise Exception(error_message)
        
        else:
            raise ValueError(f"Invalid action_mode: {action_mode}. Must be 'delete' or 'alert'")
        
        return results