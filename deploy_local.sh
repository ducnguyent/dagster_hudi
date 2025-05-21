#!/bin/bash

# Build images
docker compose -f deployment/docker-compose.yml --env-file .env build

# Deploy
docker compose -f deployment/docker-compose.yml --env-file .env up -d