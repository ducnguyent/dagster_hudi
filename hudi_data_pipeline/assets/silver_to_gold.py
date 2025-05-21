from dagster import asset, AssetExecutionContext
import pyspark.sql.functions as F
from typing import Dict, Any, List

from resources.hudi import HudiBatchProcessor
from utils.time_utils import format_hudi_timestamp

@asset(
    required_resource_keys={"spark_resource", "hudi_config"},
    deps=["bronze_to_silver_transform"],
    group_name="hudi_processing",
    io_manager_key="fs_io_manager",
    description="Transform silver data to gold aggregated tables for analytics"
)
def silver_to_gold_aggregate(context: AssetExecutionContext) -> Dict[str, Any]:
    """
    Transform silver data to gold aggregated tables for analytics.
    """
    # Get resources
    spark = context.resources.spark_resource.get_spark_session()
    hudi_config = context.resources.hudi_config
    
    # Get metadata from upstream asset
    upstream_output = context.assets_def.compute_output_for_input(
        "bronze_to_silver_transform",
        context
    )
    
    start_timestamp = upstream_output["start_time"]
    end_timestamp = upstream_output["end_time"]
    batch_id = upstream_output["batch_id"]
    
    # Create batch processor for silver table
    silver_processor = HudiBatchProcessor(
        spark=spark,
        hudi_config=hudi_config,
        table_name=hudi_config.silver_table
    )
    
    # Read incremental batch from silver
    context.log.info(f"Reading incremental data from {hudi_config.silver_table} from {start_timestamp} to {end_timestamp}")
    silver_df = silver_processor.read_incremental_batch(start_timestamp, end_timestamp)
    
    silver_count = silver_df.count()
    context.log.info(f"Aggregating {silver_count} silver records for gold layer")
    
    if silver_count == 0:
        context.log.info("No new data to process in this batch")
        return {**upstream_output, "gold_record_count": 0}
    
    # Apply multiple gold aggregations
    aggregations = create_gold_aggregations(silver_df, batch_id)
    
    # Process each aggregation
    gold_counts = {}
    for agg_name, agg_df in aggregations.items():
        full_table_name = hudi_config.get_gold_table_name(f"agg_{agg_name}")
        
        # Write to gold Hudi table
        gold_processor = HudiBatchProcessor(
            spark=spark,
            hudi_config=hudi_config,
            table_name=full_table_name
        )
        
        agg_count = agg_df.count()
        context.log.info(f"Writing {agg_count} aggregated records to {full_table_name}")
        
        gold_processor.write_batch_to_hudi(df=agg_df)
        
        gold_counts[agg_name] = agg_count
    
    # Return batch metadata with gold counts
    return {
        **upstream_output, 
        "gold_aggregations": gold_counts,
        "total_gold_records": sum(gold_counts.values())
    }

def create_gold_aggregations(df, batch_id) -> Dict[str, Any]:
    """Create multiple gold aggregation tables"""
    # Filter to valid records
    valid_df = df.filter(F.col("is_valid") == True)
    
    # 1. Category aggregation
    category_agg = (
        valid_df
        .groupBy("category_code", "dt")
        .agg(
            F.count("id").alias("transaction_count"),
            F.sum("amount").alias("total_amount"),
            F.avg("amount").alias("avg_amount"),
            F.max("amount").alias("max_amount"),
            F.min("amount").alias("min_amount"),
            F.stddev("amount").alias("stddev_amount")
        )
        .withColumn("processed_at", F.current_timestamp())
        .withColumn("batch_id", F.lit(batch_id))
        .withColumn("agg_key", F.concat(F.col("category_code"), F.lit("_"), F.col("dt")))
    )
    
    # 2. Hourly aggregation
    hourly_agg = (
        valid_df
        .withColumn("hour", F.hour(F.col("ts")))
        .groupBy("dt", "hour")
        .agg(
            F.count("id").alias("transaction_count"),
            F.sum("amount").alias("total_amount"),
            F.countDistinct("customer_id").alias("unique_customers")
        )
        .withColumn("processed_at", F.current_timestamp())
        .withColumn("batch_id", F.lit(batch_id))
        .withColumn("agg_key", F.concat(F.col("dt"), F.lit("_"), F.col("hour")))
    )
    
    return {
        "by_category": category_agg,
        "by_hour": hourly_agg
    }