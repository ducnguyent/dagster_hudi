from dagster import ScheduleDefinition
from jobs.hudi_jobs import hudi_processing_job

# Main 5-minute schedule
five_minute_schedule = ScheduleDefinition(
    name="hudi_5min_incremental_schedule",
    cron_schedule="*/5 * * * *",  # Every 5 minutes
    job=hudi_processing_job,
    execution_timezone="UTC",
    environment_vars={
        "SPARK_CONF_DIR": "/etc/spark/conf",
        "HADOOP_CONF_DIR": "/etc/hadoop/conf"
    }
)

# # Daily summary job
# daily_summary_schedule = ScheduleDefinition(
#     name="hudi_daily_summary",
#     cron_schedule="0 1 * * *",  # 1 AM daily
#     job=monitored_hudi_job,
#     execution_timezone="UTC"
# )