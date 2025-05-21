# Hudi Data Pipeline with Dagster

A modular data pipeline to process Hudi data from bronze to silver and gold layers using Apache Spark and Dagster. The pipeline runs in 5-minute mini-batches, utilizing Hudi's incremental processing capabilities.

## Features

- Incremental data processing using Hudi's timeline capabilities
- Automatic 5-minute batch scheduling with Dagster
- Transformation of bronze data to silver layer with business rules
- Aggregation of silver data into gold analytics tables
- Container-ready with Docker and Kubernetes deployment options
- Clear separation of concerns with modular design

## Architecture

The pipeline follows a layered architecture:

1. **Bronze Layer**: Raw data ingested from source systems
2. **Silver Layer**: Cleansed and validated data with business rules applied
3. **Gold Layer**: Aggregated data optimized for analytics and reporting

## Getting Started

### Prerequisites

- Python 3.10+
- Apache Spark 3.5+
- Apache Hudi 1.0.2+
- Docker and Docker Compose (for local deployment)

### Installation

1. Clone the repository:
`git clone https://github.com/yourusername/hudi-data-pipeline.git`
`cd hudi-data-pipeline`

2. Install dependencies:
`pip install -e ".[dev]"`

3. Configure your Hudi paths in `configs/hudi_config.yaml`

### Running Locally

1. Start the Dagster UI:
`dagit -f hudi_data_pipeline/definitions.py`

2. Or use Docker Compose:
`cd deployment`
`docker-compose up`

3. Visit http://localhost:3000 to access the Dagster UI

## Deployment

### Kubernetes

1. Update the Kubernetes configuration in `deployment/kubernetes/`
2. Apply the configuration:
`kubectl apply -f deployment/kubernetes/dagster.yaml`
`kubectl apply -f deployment/kubernetes/spark-operator.yaml`

## Project Structure
hudi_data_pipeline/
├── assets/               # Data assets (silver, gold)
├── jobs/                 # Job definitions
├── resources/            # Resource definitions (Spark, Hudi)
├── schedules/            # Schedule definitions
├── utils/                # Utility functions
└── definitions.py        # Main Dagster definitions

## Configuration

- Spark configurations in `configs/spark_config.yaml`
- Hudi configurations in `configs/hudi_config.yaml`
- Environment-specific configs in `configs/local.yaml`

## License

This project is licensed under the MIT License - see the LICENSE file for details.