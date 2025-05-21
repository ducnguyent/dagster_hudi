from dagster import asset, AssetExecutionContext
import pyspark.sql.functions as F
from pyspark.sql import DataFrame
from typing import Dict, Any

from resources.hudi import HudiBatchProcessor
from utils.time_utils import get_batch_time_window, format_hudi_timestamp, get_batch_metadata

@asset(
    required_resource_keys={"spark_resource", "hudi_config"},
    group_name="hudi_processing",
    io_manager_key="fs_io_manager",
    description="Transform bronze data to silver by applying business rules and data quality checks"
)
def bronze_to_silver_transform(context: AssetExecutionContext) -> Dict[str, Any]:
    """
    Transform bronze data to silver by applying business rules and data quality checks.
    Uses incremental processing via Hudi.
    """
    # Get resources
    spark = context.resources.spark_resource.get_spark_session()
    hudi_config = context.resources.hudi_config
    
    # Get time window for this batch
    start_time, end_time = get_batch_time_window(minutes=5)
    start_timestamp = format_hudi_timestamp(start_time)
    end_timestamp = format_hudi_timestamp(end_time)
    
    # Create batch processor for bronze table
    bronze_processor = HudiBatchProcessor(
        spark=spark,
        hudi_config=hudi_config,
        table_name=hudi_config.bronze_table
    )
    
    # Read incremental batch from bronze table
    context.log.info(f"Reading incremental data from {hudi_config.bronze_table} from {start_timestamp} to {end_timestamp}")
    bronze_df = bronze_processor.read_incremental_batch(start_timestamp, end_timestamp)
    
    # Get record count for logging
    bronze_count = bronze_df.count()
    context.log.info(f"Processing {bronze_count} records for silver layer")
    
    if bronze_count == 0:
        context.log.info("No new data to process in this batch")
        return get_batch_metadata(start_time, end_time)
    
    # Apply silver transformations
    silver_df = transform_to_silver(bronze_df, context)
    
    # Write transformed data to silver Hudi table
    silver_processor = HudiBatchProcessor(
        spark=spark,
        hudi_config=hudi_config,
        table_name=hudi_config.silver_table
    )
    
    context.log.info(f"Writing {silver_df.count()} records to {hudi_config.silver_table}")
    silver_processor.write_batch_to_hudi(df=silver_df)
    
    # Return batch metadata
    batch_metadata = get_batch_metadata(start_time, end_time)
    batch_metadata["bronze_record_count"] = bronze_count
    batch_metadata["silver_record_count"] = silver_df.count()
    
    return batch_metadata

def transform_to_silver(df: DataFrame, context: AssetExecutionContext) -> DataFrame:
    """Apply all transformations to convert bronze data to silver format"""
    # Add processing timestamp
    df = df.withColumn("processed_at", F.current_timestamp())
    
    # Apply data type conversions
    df = df.withColumn("amount", F.col("amount").cast("double"))
    df = df.withColumn("quantity", F.col("quantity").cast("integer"))
    df = df.withColumn("transaction_date", F.to_date(F.col("transaction_date")))
    
    # Data validation
    df = df.withColumn("is_valid", F.when(F.col("amount") > 0, True).otherwise(False))
    
    # Add calculated fields
    df = df.withColumn("category_code", F.upper(F.col("category")))
    df = df.withColumn("dt", F.date_format(F.col("transaction_date"), "yyyy-MM-dd"))
    
    # Add data quality metrics
    df = df.withColumn("has_customer_id", F.col("customer_id").isNotNull())
    
    # Apply any business rules
    df = df.withColumn("discount_amount", 
                       F.when(F.col("discount_pct").isNotNull(), 
                             F.col("amount") * F.col("discount_pct"))
                       .otherwise(F.lit(0.0)))
    
    return df