from typing import List, Dict, Any, Optional
from pyspark.sql import DataFrame, SparkSession
from dagster import ConfigurableResource
import datetime

class HudiConfigResource(ConfigurableResource):
    """Resource that provides Hudi configuration to assets"""
    base_path: str
    bronze_table: str
    silver_table: str
    gold_table_prefix: str
    tables_config: Dict[str, Any]
    
    def get_table_config(self, table_name: str) -> Dict[str, Any]:
        """Get configuration for a specific table"""
        return self.tables_config.get(table_name, {})
    
    def get_table_path(self, table_name: str) -> str:
        """Get the full path for a table"""
        return f"{self.base_path}/{table_name}"
    
    def get_gold_table_name(self, suffix: str) -> str:
        """Get the full name for a gold table"""
        return f"{self.gold_table_prefix}_{suffix}"

class HudiBatchProcessor:
    """Utility for processing incremental batches with Hudi"""
    
    def __init__(self, spark, hudi_config: HudiConfigResource, table_name: str):
        self.spark = spark
        self.hudi_config = hudi_config
        self.table_name = table_name
        self.table_path = hudi_config.get_table_path(table_name)
        self.table_config = hudi_config.get_table_config(table_name)
    
    def read_incremental_batch(self, start_timestamp, end_timestamp):
        """
        Read incremental data from Hudi table between timestamps
        
        Args:
            start_timestamp: Beginning timestamp for incremental query
            end_timestamp: Ending timestamp for incremental query
            
        Returns:
            DataFrame with incremental data
        """
        query = (
            self.spark.read.format("hudi")
            .option("hoodie.datasource.query.type", "incremental")
            .option("hoodie.datasource.read.begin.instanttime", start_timestamp)
            .option("hoodie.datasource.read.end.instanttime", end_timestamp)
            .load(self.table_path)
        )
        return query
    
    def write_batch_to_hudi(
        self, 
        df: DataFrame, 
        operation: str = "upsert"
    ):
        """
        Write data to Hudi with configuration from the resource
        
        Args:
            df: DataFrame to write
            operation: Hudi operation (upsert, insert, bulk_insert)
        """
        # Get table-specific configuration
        partition_fields = self.table_config.get("partition_fields", ["dt"])
        record_key_field = self.table_config.get("record_key_field", "id")
        precombine_field = self.table_config.get("precombine_field", "ts")
        table_type = self.table_config.get("table_type", "COPY_ON_WRITE")
        
        hudi_options = {
            'hoodie.table.name': self.table_name,
            'hoodie.datasource.write.recordkey.field': record_key_field,
            'hoodie.datasource.write.partitionpath.field': ','.join(partition_fields),
            'hoodie.datasource.write.table.name': self.table_name,
            'hoodie.datasource.write.operation': operation,
            'hoodie.datasource.write.precombine.field': precombine_field,
            'hoodie.upsert.shuffle.parallelism': '100',
            'hoodie.insert.shuffle.parallelism': '100',
            'hoodie.table.type': table_type
        }
        
        df.write.format("hudi") \
            .options(**hudi_options) \
            .mode("append") \
            .save(self.table_path)
    
    def read_snapshot(self):
        """Read the latest snapshot of the Hudi table"""
        return self.spark.read.format("hudi").load(self.table_path)
    
    def table_exists(self):
        """Check if the Hudi table exists"""
        try:
            # Try to read metadata
            self.spark.read.format("hudi").option("hoodie.datasource.query.type", "metadata").load(self.table_path)
            return True
        except Exception:
            return False