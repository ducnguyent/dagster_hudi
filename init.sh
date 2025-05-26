#!bin/bash

# Check if the Docker network already exists
if docker network inspect dagster_hudi_network >/dev/null 2>&1; then
    echo "Docker network 'dagster_hudi_network' already exists."
else
    echo "Creating Docker network 'dagster_hudi_network'."
fi
# Create the Docker network if it does not exist
docker network rm dagster_hudi_network 2>/dev/null || true
docker network create dagster_hudi_network

# Start the Docker containers using the docker-compose file
docker compose -f ./deployment/init-docker-compose.yml --env-file .env up -d