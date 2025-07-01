import argparse
import logging
import sys
from databricks.sdk import WorkspaceClient
from .factories.resource_factory import ResourceHandlerFactory
from .utils.config import ConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Monitor Databricks resources and enforce whitelist policies'
    )
    
    parser.add_argument(
        '--resource-type',
        type=str,
        required=True,
        choices=ResourceHandlerFactory.get_supported_types(),
        help='Type of resource to monitor'
    )
    
    parser.add_argument(
        '--action-mode',
        type=str,
        required=True,
        choices=['delete', 'alert'],
        help='Action to take for resources not in whitelist'
    )
    
    parser.add_argument(
        '--whitelist-path',
        type=str,
        default=None,
        help='Custom path to whitelist JSON file (optional)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode (identify violations without taking action)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the resource monitor job."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        logger.info(f"Starting resource monitor for {args.resource_type}")
        logger.info(f"Action mode: {args.action_mode}")
        logger.info(f"Dry run: {args.dry_run}")
        
        # Initialize Databricks client
        # The SDK automatically uses the environment's authentication
        client = WorkspaceClient()
        
        # Load whitelist
        try:
            whitelist = ConfigLoader.load_whitelist(
                args.resource_type, 
                args.whitelist_path
            )
        except FileNotFoundError:
            logger.error(
                f"Whitelist file not found for resource type: {args.resource_type}. "
                f"Please create a whitelist file or specify --whitelist-path"
            )
            sys.exit(1)
        
        # Create handler
        handler = ResourceHandlerFactory.create_handler(
            args.resource_type,
            client,
            whitelist
        )
        
        # Check resources
        violations = handler.check_resources(dry_run=args.dry_run)
        
        if not violations:
            logger.info("No violations found. All resources are whitelisted.")
            return
        
        # Handle violations if not in dry-run mode
        if not args.dry_run:
            logger.info(f"Handling {len(violations)} violations with action: {args.action_mode}")
            results = handler.handle_violations(args.action_mode)
            
            if args.action_mode == 'delete':
                logger.info(f"Action summary: {results}")
                
                if results['status'] == 'partial_failure':
                    logger.error("Some actions failed. Check logs for details.")
                    sys.exit(1)
        else:
            # In dry-run mode, just report what would happen
            logger.info(f"[DRY RUN] Would handle {len(violations)} violations:")
            for violation in violations:
                logger.info(f"[DRY RUN] - {violation['id']}: {violation['details']}")
            
            if args.action_mode == 'alert':
                logger.info("[DRY RUN] Would raise exception to trigger email alerts")
            else:
                logger.info(f"[DRY RUN] Would delete {len(violations)} resources")
        
        logger.info("Resource monitoring completed successfully")
        
    except Exception as e:
        logger.error(f"Job failed with error: {str(e)}")
        # Re-raise to ensure job failure is properly reported
        raise


if __name__ == "__main__":
    main()