#!/bin/bash

# Arguments
NAME=$1
LOCATION=$2

if [ -z "$NAME" ] || [ -z "$LOCATION" ]; then
  echo "Usage: ./create_component.sh ComponentName ./relative/path"
  exit 1
fi

ng generate component "$LOCATION/$NAME" --standalone --style=scss

# This file permit the creation of Angular component.
# Example : ./create_component.sh my-modal shared/modals