#!/bin/bash

n=5  # number of hours to let it run before restart

while true; do
  echo "Starting script at $(date)"
  timeout $((n * 3600)) python3 main.py
  echo "Restarting script after $n hour(s)..."
done
