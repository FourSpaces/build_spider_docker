#!/usr/bin/env bash
# Created by paincompiler on 2018/08/25

##########settings##########
set -o errexit
set -o errtrace
set -o xtrace
##########settings##########

function finish {
    # cleanup code here

    if [[ -z "${ZXZL_DOCKER_REGISTRY_HOST// }" ]]; then
        # docker registry not set
        IMAGE_TAG=crawler/${PROJECT_NAME}:${GIT_COMMIT}
        sudo docker rmi -f ${IMAGE_TAG}
    else
        # build docker image
        IMAGE_TAG=${ZXZL_DOCKER_REGISTRY_HOST}/cheng1483/${PROJECT_NAME}:${GIT_COMMIT}
        sudo docker rmi -f ${IMAGE_TAG}
    fi

    NONE_IMAGE=`sudo docker images | grep "^<none>" | awk '{print $3}'`

    echo "$NONE_IMAGE"

    if [[ "$NONE_IMAGE" != "" ]]; then
        sudo docker rmi -f ${NONE_IMAGE}
    fi

    echo "cleaning up"
}

trap finish EXIT

source $(dirname $0)/utils.sh
set_basic_env

# build docker image
if [[ -z "${ZXZL_DOCKER_REGISTRY_HOST// }" ]]; then
    # docker registry not set
    IMAGE_TAG=crawler/${PROJECT_NAME}:${GIT_COMMIT}
    sudo docker build -t ${IMAGE_TAG} .
else
    # build docker image
    sudo docker login -u ${ZXZL_DOCKER_REGISTRY_USERNAME} -p ${ZXZL_DOCKER_REGISTRY_PASSWORD} ${ZXZL_DOCKER_REGISTRY_HOST}
    IMAGE_TAG=${ZXZL_DOCKER_REGISTRY_HOST}/cheng1483/${PROJECT_NAME}:${GIT_COMMIT}
    sudo docker build -t ${IMAGE_TAG} .
    sudo docker push ${IMAGE_TAG}
fi
        