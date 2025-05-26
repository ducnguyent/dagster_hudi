from dagster import resource, ConfigurableResource
from pyspark.sql import SparkSession
import yaml
import os
from typing import Dict

class SparkResource(ConfigurableResource):
    """Resource for managing SparkSession with Hudi configurations"""
    spark_config: Dict[str, str]
    app_name: str = "HudiIncrementalPipeline"
    hudi_version: str = "0.13.0"
    scala_version: str = "2.12"
    enable_hudi: bool = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._spark = None
    
    def get_spark_session(self):
        """Returns a configured SparkSession, creating one if needed"""
        if self._spark is None:
            builder = SparkSession.builder.appName(self.app_name)
            
            # Apply all spark configurations
            for key, value in self.spark_config.items():
                builder = builder.config(key, value)
            
            # Add Hudi package if enabled
            if self.enable_hudi:
                builder = builder.config(
                    "spark.jars.packages", 
                    f"org.apache.hudi:hudi-spark3-bundle_{self.scala_version}:{self.hudi_version}"
                )
                
                # Add Hudi-specific configurations
                builder = builder.config(
                    "spark.sql.extensions", 
                    "org.apache.spark.sql.hudi.HoodieSparkSessionExtension"
                )
                builder = builder.config(
                    "spark.sql.catalog.spark_catalog", 
                    "org.apache.spark.sql.hudi.catalog.HoodieCatalog"
                )
            
            self._spark = builder.getOrCreate()
        return self._spark
    
    def shutdown_spark(self):
        """Properly stop the SparkSession"""
        if self._spark is not None:
            self._spark.stop()
            self._spark = None

@resource(config_schema={"config_path": str})
def spark_session(init_context):
    """Resource that provides a configured SparkSession"""
    config_path = init_context.resource_config["config_path"]
    
    # Load config from YAML file
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Create resource
    spark_resource = SparkResource(
        spark_config=config["spark_config"],
        app_name=config.get("app_name", "HudiIncrementalPipeline"),
        hudi_version=config.get("hudi_version", "0.13.0"),
        scala_version=config.get("scala_version", "2.12"),
        enable_hudi=config.get("enable_hudi", True)
    )
    
    try:
        yield spark_resource
    finally:
        # Ensure proper cleanup
        spark_resource.shutdown_spark()