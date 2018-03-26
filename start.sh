#!/bin/bash

# start this script using the `flock` command
# flock -xn /home/pi/speedcomplainer/lock.lck -c /home/pi/speedcomplainer/start.sh
# http://bencane.com/2015/09/22/preventing-duplicate-cron-job-executions/
# https://unix.stackexchange.com/questions/107939/how-to-restart-the-python-script-automatically-if-it-is-killed-or-dies

cd /home/pi/speedcomplainer/
nohup python2 /home/pi/speedcomplainer/speedcomplainer.py > /home/pi/speedcomplainer/cronoutput.log 2>&1 &