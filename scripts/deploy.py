import os
from pathlib import Path
from dotenv import load_dotenv
from gooddata_sdk import GoodDataSdk, CatalogDataSourceSnowflake, SnowflakeAttributes, BasicCredentials, CatalogWorkspace

load_dotenv()

host = os.getenv('GOODDATA_HOST')
token = os.getenv('GOODDATA_API_TOKEN')
sdk = GoodDataSdk.create(host, token)

workspace_id = "demo_ws"
data_source_id = "demo_ds"

# First, ensure that data source exists in the org
sdk.catalog_data_source.create_or_update_data_source(
    CatalogDataSourceSnowflake(
        id=data_source_id,
        name="Demo Data Source",
        db_specific_attributes=SnowflakeAttributes(
            account=os.environ["SNOWFLAKE_ACCOUNT"],
            warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
            db_name=os.environ["SNOWFLAKE_DBNAME"]
        ),
        schema=os.environ["SNOWFLAKE_SCHEMA"],
        credentials=BasicCredentials(
            username=os.environ["SNOWFLAKE_USER"],
            password=os.environ["SNOWFLAKE_PASSWORD"],
        ),
    )
)

# Scan data source schema to ensure the latest one is present on server
sdk.catalog_data_source.scan_and_put_pdm(data_source_id=data_source_id)

# Ensure workspace exists in the org
sdk.catalog_workspace.create_or_update(
    CatalogWorkspace(
        workspace_id=workspace_id,
        name="Demo Workspace"
    )
)

# Next we need to do some trickery. Since GoodData for VS Code does not yet
# support insights and dashboards definition, but does support metric definition,
# we need to merge two formats:
# - Files under `analytics_modes` defined in Python SDK supported format
# - Files under `analytics` defined in GoodData for VS Code format
# This cumbersome steps will not be needed as we develop the tooling further

# Deploy the analytics from CLI
deploy_result = os.system("npm run deploy")

if (deploy_result != 0):
    raise Exception("Failed to deploy analytics to server") 

# Load converted analytical model from sever to receive metrics
server_am = sdk.catalog_workspace_content.get_declarative_analytics_model(
    workspace_id=workspace_id
)

# Load analytics model from disk
am = sdk.catalog_workspace_content.load_analytics_model_from_disk(
    path=Path.cwd()
)

# Merge the two modesl - taking metrics from server
am.analytics.metrics = server_am.analytics.metrics

# Deploy the result back to server
sdk.catalog_workspace_content.put_declarative_analytics_model(
    workspace_id=workspace_id,
    analytics_model=am
)
