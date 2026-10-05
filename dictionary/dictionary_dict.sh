#!/bin/bash

thisdir=$(dirname "$0")
cd $thisdir
if [[ $# -eq 0 ]]; then
    ./dictionary.py -dict $thisdir/english
else
    ./dictionary.py -dict $thisdir/english $1
fi
