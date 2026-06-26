#!/bin/bash
set -e
echo "Building image..."
docker build -t quote-api:local-scan .
echo "Scanning with Trivy (HIGH/CRITICAL, fixable only)..."


MSYS_NO_PATHCONV=1 docker run --rm \
  -v //var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest \
  image --severity HIGH,CRITICAL --ignore-unfixed quote-api:local-scan
