#!/bin/bash

function sigint() {
   echo "process got SIGINT and it is exiting ..."
   run=false
}

function sigterm() {
   echo "process got SIGTERM and it is exiting ..."
   run=false
}

trap 'sigint' INT
trap 'sigterm' TERM

mkdir -p /jsons/current/

while ${run}; do
  conflate /data/profile.py -o /data/josm.osm --changes /jsons/current/changes.json
  python3 conflate2rss.py -n /jsons/current/changes.json -i /jsons/inspected/changes.json -r /rss/rss.xml
  mv -f /jsons/current/changes.json /jsons/inspected/changes.json
  sleep ${PERIOD:-24h}
done
