#!/bin/bash

#Updating runtime.ini in controllers in order to find the conda's python interpreter
template="[python]
COMMAND = "

local_venv_path=$(which python)

# loop over all controllers
for dir in $(ls -d -F src/webots/controllers/* | grep "/$"); do
  # don't create in "__pycache__" folder!
  if [[ $dir =~ "__pycache__" ]]; then
    continue
  fi
  echo "$template$local_venv_path" > ${dir}runtime.ini
done
