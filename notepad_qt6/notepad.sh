#!/bin/bash

thisdir=$(dirname "$0")
cd $thisdir

if [[ $# -eq 0 ]]; then
    python3 notepad.py
elif [[ $# -eq 1 ]]; then
    python3 notepad.py "$1"
fi

cd $HOME
