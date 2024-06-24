#!/bin/bash

sudo python server.py &
sleep 1
python client.py &
#sleep 1
#python client.py &

