#!/usr/bin/env bash
# Created by paincompiler on 2018/08/25

##########settings##########
set -o errexit
set -o errtrace
#set -o pipefail
set -o xtrace
##########settings##########

function finish {
    # cleanup code here
    echo "cleaning up"
}

trap finish EXIT

source $(dirname $0)/utils.sh
set_basic_env

scrapyd-deploy --build-egg=${GIT_COMMIT}.egg

if [[ $# -ne 0 ]]; then
    # >= 1
    # move egg to scrapyd project dir
    mkdir $1/${PROJECT_NAME}/
    mv ${GIT_COMMIT}.egg $1/${PROJECT_NAME}/
fi
        