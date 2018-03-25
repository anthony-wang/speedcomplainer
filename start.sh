#!/bin/bash
cd /home/pi/speedcomplainer/
nohup python2 /home/pi/speedcomplainer/speedcomplainer.py > /home/pi/speedcomplainer/cronoutput.log 2>&1 &