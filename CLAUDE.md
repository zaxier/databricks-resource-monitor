# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose
This is a Databricks resource monitoring system that enforces whitelist policies on Databricks resources (Model Serving Endpoints, Apps). It can either alert via email or automatically delete unauthorized resources.

## Key Commands

### Local Development
```bash
# Install with UV (recommended)
uv pip install -e .

# Or install dependencies manually
uv pip install databricks-sdk>=0.57.0

# Run locally in dry-run mode (no actions taken)
python -m src.main --resource-type model_endpoints --action-mode alert --dry-run

# Run with deletion mode
python -m src.main --resource-type apps --action-mode delete

# Use custom whitelist
python -m src.main --resource-type model_endpoints --action-mode alert --whitelist-path /path/to/custom.json
```

### Deployment
```bash
# Set required environment variables
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-token"  # Or use other auth methods
export DATABRICKS_SERVICE_PRINCIPAL="service-principal-name"  # For production

# Deploy to different environments
databricks bundle deploy -t dev
databricks bundle deploy -t staging
databricks bundle deploy -t prod

# Deploy with custom variables
databricks bundle deploy -t prod --var="alert_email=custom@company.com" --var="schedule_cron=0 */30 * * * ?"
```

### Building
```bash
# Build wheel package (required before deployment)
uv build
```

## Architecture

### Core Pattern: Strategy + Factory
The system uses an extensible handler architecture:

1. **Abstract Base**: `ResourceHandler` (src/handlers/base.py) defines the interface:
   - `list_resources()`: Enumerate all resources of type
   - `delete_resource()`: Remove a specific resource
   - `check_resources()`: Compare against whitelist
   - `handle_violations()`: Execute alert or delete action

2. **Factory**: `ResourceHandlerFactory` (src/factories/resource_factory.py) creates handlers based on resource type

3. **Concrete Handlers**: Implement specific resource logic
   - `ModelEndpointHandler`: Uses `client.serving_endpoints.*` APIs
   - `AppsHandler`: Uses `client.apps.*` APIs

### Alert Mechanism
Since Databricks doesn't have programmatic alert creation, the system uses job failure notifications:
- In alert mode, violations trigger an exception
- Exception causes job failure
- Job failure triggers configured email notifications in databricks.yml

### Whitelist Management
- Whitelists stored in `config/whitelists/{resource_type}.json`
- Support both array format and object with description
- Loaded by `ConfigLoader` (src/utils/config.py)
- Can override with `--whitelist-path` parameter

## Adding New Resource Types

1. Create handler in `src/handlers/new_resource.py`:
```python
from .base import ResourceHandler

class NewResourceHandler(ResourceHandler):
    def list_resources(self):
        return list(self.client.new_resource.list())
    
    def delete_resource(self, resource_id):
        self.client.new_resource.delete(resource_id)
        return True
    
    # Implement other abstract methods
```

2. Register in `src/factories/resource_factory.py`:
```python
_handlers = {
    'model_endpoints': ModelEndpointHandler,
    'apps': AppsHandler,
    'new_resource': NewResourceHandler,  # Add here
}
```

3. Create whitelist: `config/whitelists/new_resource.json`

4. Optionally add job config in `databricks.yml` or `resources/*.yml`

## Important Considerations

- **Authentication**: Uses Databricks SDK auto-authentication (env vars, CLI config)
- **Production**: Must use service principal (configured in databricks.yml targets)
- **Whitelist Paths**: Default to `/Workspace/config/whitelists/` in Databricks, falls back to local paths for development
- **Job Parameters**: All parameters defined in `parse_arguments()` in src/main.py
- **Email Recipients**: Configured per target in databricks.yml variables