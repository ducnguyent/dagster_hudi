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

# # Optional: additional monitoring ops if needed
# @op(required_resource_keys={"slack"})
# def notify_on_failure(context, failure_data):
#     """Send notification on job failure"""
#     context.resources.slack.send_message(
#         channel="#data-alerts",
#         message=f"❌ Hudi batch job failed: {failure_data}"
#     )

# @op(required_resource_keys={"metrics"})
# def report_batch_metrics(context, batch_metadata):
#     """Report batch processing metrics to monitoring system"""
#     metrics = {
#         "bronze_record_count": batch_metadata.get("bronze_record_count", 0),
#         "silver_record_count": batch_metadata.get("silver_record_count", 0),
#         "gold_record_count": batch_metadata.get("total_gold_records", 0),
#         "batch_id": batch_metadata.get("batch_id"),
#         "processing_time": context.resources.metrics.get_execution_time()
#     }
    
#     context.resources.metrics.report_metrics("hudi_batch", metrics)
#     return metrics

# # Optional: Additional job with monitoring
# @job
# def monitored_hudi_job():
#     """Hudi processing job with monitoring"""
#     try:
#         # Run the asset job first
#         batch_metadata = hudi_processing_job()
#         # Then report metrics
#         report_batch_metrics(batch_metadata)
#     except Exception as e:
#         notify_on_failure({"error": str(e), "timestamp": datetime.now().isoformat()})