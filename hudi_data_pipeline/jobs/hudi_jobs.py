from datetime import datetime
from dagster import define_asset_job, AssetSelection, job, op, Out, In, Output, Nothing
from typing import Dict, Any

# Define the main job that runs both silver and gold transformations
hudi_processing_job = define_asset_job(
    name="hudi_mini_batch_job",
    selection=AssetSelection.groups("hudi_processing"),
    config={
        "execution": {
            "config": {
                "multiprocess": {
                    "max_concurrent": 1  # Ensure sequential execution
                }
            }
        }
    },
    tags={
        "owner": "data_engineering",
        "pipeline": "hudi_incremental"
    }
)
