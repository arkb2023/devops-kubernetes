#!/bin/bash
# Generates a random string every 5 seconds.
# Format: '<timestamp>: <random_string>'
RANDOM_STRING=$(cat /proc/sys/kernel/random/uuid)
while true; do
    echo "$(date -Is): $RANDOM_STRING"
    sleep 5
done