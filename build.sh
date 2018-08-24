#!/usr/bin/env bash

set -e

IMAGE=ansible-executor
DOCKER_HUB_USER=ymage

# 1. Build the docker image
docker build -t $DOCKER_HUB_USER/$IMAGE .

# Push to dockerhub
#docker tag  $IMAGE $DOCKER_HUB_USER/$IMAGE
docker push $DOCKER_HUB_USER/$IMAGE
