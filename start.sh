#!/bin/bash

# start this script using the `flock` command
# flock -xn /home/pi/speedcomplainer/lock.lck -c /home/pi/speedcomplainer/start.sh
# http://bencane.com/2015/09/22/preventing-duplicate-cron-job-executions/

cd /home/pi/speedcomplainer/
nohup python2 /home/pi/speedcomplainer/speedcomplainer.py > /home/pi/speedcomplainer/cronoutput.log 2>&1 &