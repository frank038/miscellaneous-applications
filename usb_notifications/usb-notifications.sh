#!/bin/bash

thisdir=$(dirname "$0")
cd $thisdir

python3 usb-notifications.py &

cd $HOME
