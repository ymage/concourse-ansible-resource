#!/usr/bin/env bash
set -euo pipefail

IMAGE=ansible-executor
DOCKER_HUB_USER=ymage
VERSION=$(date "+%Y%m%d%H%M")

echo "Build ${IMAGE}:${VERSION}"

# 1. Build the docker image
docker build --build-arg ${VERSION} -t ${DOCKER_HUB_USER}/${IMAGE}:${VERSION} .

# Push to dockerhub
docker push ${DOCKER_HUB_USER}/${IMAGE}:${VERSION}
