# Databricks Resource Monitor

A flexible and extensible Databricks job for monitoring and managing Databricks resources based on whitelist policies. Currently supports Model Serving Endpoints and Databricks Apps, with easy extensibility for additional resource types.

## Features

- **Whitelist-based monitoring**: Define allowed resources in JSON configuration files
- **Dual action modes**: Choose between alerting or automatic deletion of unauthorized resources
- **Email notifications**: Automatic alerts when violations are detected
- **Extensible architecture**: Easy to add new resource types
- **Dry-run mode**: Test policies without taking action
- **Databricks Asset Bundle deployment**: Simple deployment and management

## Architecture

The system uses a strategy pattern with:
- Abstract `ResourceHandler` base class
- Concrete handlers for each resource type (Model Endpoints, Apps)
- Factory pattern for handler creation
- Configuration-driven whitelist management

## Setup

### Prerequisites

- Python 3.12+
- [UV](https://docs.astral.sh/uv/) package manager (recommended) or pip
- Databricks CLI configured with authentication
- Databricks workspace with appropriate permissions

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd databricks-resource-monitor
```

2. Install with UV (recommended):
```bash
# Install in development mode
uv pip install -e .

# Or install specific dependencies
uv pip install databricks-sdk>=0.57.0
```

Alternatively with pip:
```bash
pip install -e .
```

3. Configure whitelists in `config/whitelists/`:
   - `model_endpoints.json` - Allowed model serving endpoints
   - `apps.json` - Allowed Databricks apps

## Development

### Development Setup

1. Install UV if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create a virtual environment and install in development mode:
```bash
# UV automatically manages virtual environments
uv pip install -e .
```

3. Install development dependencies (if any):
```bash
uv pip install pytest black ruff  # Add as needed
```

### Iterative Development Workflow

1. **Make code changes** to files in `src/databricks_resource_monitor/`

2. **Test locally** in dry-run mode:
```bash
# Test without making changes
python -m databricks_resource_monitor.main --resource-type model_endpoints --action-mode alert --dry-run

# Test with custom whitelist
python -m databricks_resource_monitor.main --resource-type apps --action-mode alert --whitelist-path ./config/whitelists/apps.json --dry-run
```

3. **Build and test the package**:
```bash
# Build wheel for deployment
uv build

# Install and test the console script
uv pip install dist/*.whl
databricks-resource-monitor --resource-type model_endpoints --action-mode alert --dry-run
```

4. **Deploy to development environment**:
```bash
databricks bundle deploy -t dev
```

5. **Test the deployed job** in Databricks workspace

### Development Tips

- Use `--dry-run` flag extensively during development to avoid unintended actions
- Test both `alert` and `delete` modes with different resource types
- Create test whitelist files to validate different scenarios
- Check logs in Databricks workspace after deployment testing
- Use different target environments (`dev`, `staging`, `prod`) for progressive testing

### Hot Reloading During Development

Since this is a batch job (not a web service), there's no hot reloading. However, you can:

1. **Make changes** to your code
2. **Re-run locally** with `python -m databricks_resource_monitor.main ...`
3. **Rebuild and redeploy** when ready: `uv build && databricks bundle deploy -t dev`

### Whitelist Configuration

Whitelist files support two formats:

**Simple array format:**
```json
["endpoint-1", "endpoint-2", "app-1"]
```

**Object format with description:**
```json
{
  "description": "Production model endpoints",
  "whitelist": ["prod-model-1", "prod-model-2"]
}
```

## Deployment

### Using Databricks Asset Bundles

1. Set environment variables:
```bash
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="your-token"  # Or use other auth methods
```

2. Deploy to development:
```bash
databricks bundle deploy -t dev
```

3. Deploy to production:
```bash
databricks bundle deploy -t prod
```

### Configuration Variables

The bundle supports these variables:
- `alert_email`: Email for notifications (default: alerts@company.com)
- `schedule_cron`: Cron expression for job schedule (default: every 6 hours)

Override in deployment:
```bash
databricks bundle deploy -t prod --var="alert_email=prod-alerts@company.com"
```

## Usage

### Running Locally

Test the monitor locally:

```bash
# Check model endpoints (dry run)
python -m databricks_resource_monitor.main --resource-type model_endpoints --action-mode alert --dry-run

# Delete unauthorized apps
python -m databricks_resource_monitor.main --resource-type apps --action-mode delete

# Use custom whitelist
python -m databricks_resource_monitor.main --resource-type model_endpoints --action-mode alert --whitelist-path /path/to/custom.json
```

### Job Parameters

When the job runs in Databricks, it accepts these parameters:
- `--resource-type`: Type of resource to monitor (`model_endpoints`, `apps`)
- `--action-mode`: Action for violations (`alert`, `delete`)
- `--whitelist-path`: Optional custom whitelist path
- `--dry-run`: Test mode without taking actions

### Action Modes

1. **Alert Mode**: 
   - Identifies unauthorized resources
   - Raises exception with detailed report
   - Triggers email notifications via job failure

2. **Delete Mode**:
   - Identifies and automatically deletes unauthorized resources
   - Logs all actions taken
   - Continues even if some deletions fail

## Extending the System

### Adding a New Resource Type

1. Create a new handler in `src/databricks_resource_monitor/handlers/`:
```python
from .base import ResourceHandler

class MyResourceHandler(ResourceHandler):
    def list_resources(self):
        # Implementation
    
    def delete_resource(self, resource_id):
        # Implementation
    
    # Implement other required methods
```

2. Register in `src/databricks_resource_monitor/factories/resource_factory.py`:
```python
_handlers = {
    'model_endpoints': ModelEndpointHandler,
    'apps': AppsHandler,
    'my_resource': MyResourceHandler,  # Add your handler
}
```

3. Create whitelist file: `config/whitelists/my_resource.json`

4. Optionally add a job configuration in `databricks.yml` or `resources/`

## Monitoring and Alerts

### Email Notifications

Configure email recipients in `databricks.yml`:
- `on_failure`: Notified when violations are found (alert mode) or deletions fail
- `on_success`: Notified on successful completion
- `on_start`: Notified when job starts

### Logs

Access job logs in Databricks:
1. Navigate to Workflows
2. Select the resource monitor job
3. View run history and logs

## Security Considerations

1. **Service Principal**: Use service principal for production deployments
2. **Permissions**: Ensure appropriate permissions for listing/deleting resources
3. **Whitelist Security**: Store whitelists in secure locations
4. **Audit Trail**: All actions are logged for compliance

## Troubleshooting

### Common Issues

1. **Whitelist not found**:
   - Ensure whitelist files exist in `config/whitelists/`
   - Check file permissions
   - Verify JSON syntax

2. **Authentication errors**:
   - Verify Databricks CLI configuration
   - Check workspace URL and token
   - Ensure service principal has required permissions

3. **Job failures**:
   - Check job logs for detailed error messages
   - Verify cluster configuration
   - Ensure Python dependencies are installed

### Debug Mode

Enable detailed logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

[Your License Here]