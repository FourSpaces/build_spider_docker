#!/usr/bin/env bash
# Created by paincompiler on 2018/08/25

##########settings##########
set -o errtrace
set -o nounset
set -o pipefail
set -o xtrace
##########settings##########

function finish {
    # cleanup code here
    echo "cleaning up"
}

trap finish EXIT

# script here

if [ ! -d "spiderkeeper" ]; then
  mkdir spiderkeeper
fi

# nohup scrapymon --auth='xyx:xyx' --server=http://0.0.0.0:6800 > scrapymon/log &
nohup spiderkeeper --port=6500 --username='xyx'  --password='xyx233' --server=http://0.0.0.0:6800 &
scrapyd
        