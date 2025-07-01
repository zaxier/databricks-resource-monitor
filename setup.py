from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="databricks_resource_monitor",
    version="1.0.0",
    description="Monitor and manage Databricks resources based on whitelist policies",
    packages=find_packages(),
    package_dir={"": "src"},
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "databricks-resource-monitor=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["config/whitelists/*.json"],
    },
)