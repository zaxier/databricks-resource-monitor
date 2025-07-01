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
python -m databricks_resource_monitor --resource-type model_endpoints --action-mode alert --dry-run

# Run with deletion mode
python -m databricks_resource_monitor --resource-type apps --action-mode delete

# Use custom whitelist
python -m databricks_resource_monitor --resource-type model_endpoints --action-mode alert --whitelist-path /path/to/custom.json

# Use console script (after installation)
databricks-resource-monitor --resource-type model_endpoints --action-mode alert --dry-run
```

### Deployment
```bash
# Set required environment variables
databricks auth login --host <workspace_url> --profile <profile_name>
# Deploy to different environments
databricks bundle deploy -t dev --profile <profile_name>
databricks bundle deploy -t staging --profile <profile_name>
databricks bundle deploy -t prod --profile <profile_name>

# Deploy with custom variables
databricks bundle deploy -t prod --var="alert_email=custom@company.com"
```

## Architecture

### Core Pattern: Strategy + Factory
The system uses an extensible handler architecture:

1. **Abstract Base**: `ResourceHandler` (src/databricks_resource_monitor/handlers/base.py) defines the interface:
   - `list_resources()`: Enumerate all resources of type
   - `delete_resource()`: Remove a specific resource
   - `check_resources()`: Compare against whitelist
   - `handle_violations()`: Execute alert or delete action

2. **Factory**: `ResourceHandlerFactory` (src/databricks_resource_monitor/factories/resource_factory.py) creates handlers based on resource type

3. **Concrete Handlers**: Implement specific resource logic
   - `ModelEndpointHandler`: Uses `client.serving_endpoints.*` APIs
   - `AppsHandler`: Uses `client.apps.*` APIs

### Alert Mechanism
Since Databricks doesn't have programmatic alert creation (alerts currently in Beta), the system uses job failure notifications:
- In alert mode, violations trigger an exception
- Exception causes job failure
- Job failure triggers configured email notifications in databricks.yml

### Whitelist Management
- Whitelists embedded in package at `src/databricks_resource_monitor/config/whitelists/{resource_type}.json`
- Fallback to `/Workspace/config/whitelists/{resource_type}.json` in Databricks
- Support both array format and object with description plus filtering options
- Enhanced `ResourceConfig` supports `ignore_databricks_managed` flag
- Loaded by `ConfigLoader` (src/databricks_resource_monitor/utils/config.py)
- Can override with `--whitelist-path` parameter

## Adding New Resource Types

1. Create handler in `src/databricks_resource_monitor/handlers/new_resource.py`:
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

2. Register in `src/databricks_resource_monitor/factories/resource_factory.py`:
```python
_handlers = {
    'model_endpoints': ModelEndpointHandler,
    'apps': AppsHandler,
    'new_resource': NewResourceHandler,  # Add here
}
```

3. Create whitelist: `src/databricks_resource_monitor/config/whitelists/new_resource.json`

4. Optionally add job config in `databricks.yml` or `resources/*.yml`

## Important Considerations

- **Authentication**: Uses Databricks SDK auto-authentication (env vars, CLI config)
- **Whitelist Paths**: Loaded from package resources first, fallback to `/Workspace/config/whitelists/` in Databricks, then local paths for development
- **Job Parameters**: All parameters defined in `parse_arguments()` in src/databricks_resource_monitor/main.py
- **Email Recipients**: Configured per target in databricks.yml variables