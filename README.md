# Databricks Resource Monitor

Monitor and manage Databricks resources (Model Serving Endpoints, Apps) based on whitelist policies. Supports both alerting and automatic deletion of unauthorized resources.

## Prerequisites

- Python 3.12+
- [Databricks CLI](https://docs.databricks.com/dev-tools/cli/index.html) - **Required dependency**
- [UV](https://docs.astral.sh/uv/) package manager (recommended)

## Quick Start

### 1. Install

```bash
git clone <repository-url>
cd databricks-resource-monitor
uv pip install -e .
```

### 2. Authenticate with Databricks

```bash
# Login and create a profile
databricks auth login --host https://your-workspace.cloud.databricks.com --profile my-profile

```

### 3. Run Locally

```bash
# Dry run (recommended first)
python -m databricks_resource_monitor --resource-type model_endpoints --action-mode alert --dry-run --profile my-profile

# Alert mode with profile
python -m databricks_resource_monitor --resource-type model_endpoints --action-mode alert --profile my-profile

# Delete mode with profile
python -m databricks_resource_monitor --resource-type apps --action-mode delete --profile my-profile

```

### 4. Deploy to Databricks

```bash
# Deploy with profile
databricks bundle deploy -t dev --profile my-profile
databricks bundle deploy -t prod --profile my-profile --var="alert_email=alerts@company.com"
```

## Configuration

### Whitelists

Whitelists are embedded in the package at `src/databricks_resource_monitor/config/whitelists/`. Each resource type requires its own whitelist file (e.g., `model_endpoints.json`, `apps.json`).

**Whitelist format:**
```json
{
  "description": "Production resources",
  "whitelist": ["prod-model-1", "prod-model-2"],
  "ignore_databricks_managed": true
}
```

### Parameters

- `--resource-type`: `model_endpoints` or `apps`
- `--action-mode`: `alert` (raises exception) or `delete` (removes resources)
- `--profile`: Databricks CLI profile to use
- `--whitelist-path`: Custom whitelist file path
- `--dry-run`: Test mode without taking actions

## How It Works

1. **Alert Mode**: Finds violations → raises exception → job fails → email sent
2. **Delete Mode**: Finds violations → deletes resources → logs actions
3. **Whitelist Loading**: Package resources → workspace paths → local fallback
4. **Authentication**: Uses Databricks CLI profiles or environment variables

## Adding New Resource Types

1. Create handler in `src/databricks_resource_monitor/handlers/new_resource.py`
2. Register in `src/databricks_resource_monitor/factories/resource_factory.py`
3. Add whitelist: `src/databricks_resource_monitor/config/whitelists/new_resource.json`

## Development

```bash
# Make changes and test
python -m databricks_resource_monitor --resource-type model_endpoints --action-mode alert --dry-run --profile dev

# Build and redeploy
uv build && databricks bundle deploy -t dev --profile dev
```

## Troubleshooting

- **Authentication**: Verify `databricks auth profiles` shows your profile
- **Permissions**: Ensure profile has access to list/delete resources
- **Whitelists**: Check JSON syntax and file paths
- **Logs**: View in Databricks Workflows → job runs

## License

MIT License - see [LICENSE](LICENSE) file for details.