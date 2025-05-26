from dagster import (
    Definitions, 
    FilesystemIOManager,
    load_assets_from_modules,
    file_relative_path
)
import os
import yaml

from assets import bronze_to_silver, silver_to_gold
from jobs.hudi_jobs import hudi_processing_job
from schedules.schedules import five_minute_schedule
from resources.spark import SparkResource
from resources.hudi import HudiConfigResource

# Load assets
assets = load_assets_from_modules([bronze_to_silver, silver_to_gold])

# Load config
def get_config(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

# Path to config files
config_dir = file_relative_path(__file__, "../configs")
spark_config_path = os.path.join(config_dir, "spark_config.yaml")
hudi_config_path = os.path.join(config_dir, "hudi_config.yaml")

# Load configurations
spark_config = get_config(spark_config_path)
hudi_config = get_config(hudi_config_path)

# Resources configuration
resources = {
    "spark_resource": SparkResource(
        spark_config=spark_config.get("spark_config", {}),
        app_name=spark_config.get("app_name", "HudiIncrementalPipeline"),
        hudi_version=spark_config.get("hudi_version", "1.0.2"),
        enable_hudi=True
    ),
    "hudi_config": HudiConfigResource(
        base_path=hudi_config.get("base_path", "/path/to/hudi/tables"),
        bronze_table=hudi_config.get("bronze_table", "bronze_events"),
        silver_table=hudi_config.get("silver_table", "silver_events"),
        gold_table_prefix=hudi_config.get("gold_table_prefix", "gold"),
        tables_config=hudi_config.get("tables", {})
    ),
    "fs_io_manager": FilesystemIOManager(
        base_dir=os.getenv("DAGSTER_FS_IO_BASE_DIR", "/tmp/dagster/storage")
    )
}

# # Optional: Add Slack for notifications if available
# try:
#     from dagster_slack import SlackResource
#     resources["slack"] = SlackResource(
#         token=EnvVar("SLACK_TOKEN"),
#         default_channel="#data-alerts"
#     )
# except ImportError:
#     pass

# Main Dagster definitions
defs = Definitions(
    assets=assets,
    jobs=[hudi_processing_job],
    schedules=[five_minute_schedule],
    resources=resources
)