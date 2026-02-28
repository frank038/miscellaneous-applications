#!/bin/bash

thisdir=$(dirname "$0")
cd $thisdir

LD_PRELOAD=./libgtk4-layer-shell.so.1.0.4 python3 wdesktop.py
