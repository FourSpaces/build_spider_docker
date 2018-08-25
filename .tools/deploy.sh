#!/usr/bin/env bash
# Created by paincompiler on 2018/08/25

##########settings##########
set -o errexit
set -o errtrace
set -o xtrace
##########settings##########

function finish {
    # cleanup code here
    echo "cleaning up"
}

trap finish EXIT

source $(dirname $0)/utils.sh
set_basic_env
#curl -v http://deployer.io:9001/deploy/${PROJECT_NAME}/${PROJECT_ENV}/${GIT_COMMIT}
        