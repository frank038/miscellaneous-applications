#!/bin/bash

thisdir=$(dirname "$0")
cd $thisdir
if [[ $# -eq 0 ]]; then
    ./dictionary.py -curl
else
    ./dictionary.py -curl $1
fi
