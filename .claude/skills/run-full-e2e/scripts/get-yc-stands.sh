#!/usr/bin/env bash

set -uo pipefail nounset

export YC_TOKEN=$DEV_YC_TOKEN

echo "INFO: get VM data from the cloud"
yc compute instance list --folder-id $DEV_FOLDER_ID \
    --format json | jq '.[] | {name, created_at, labels}'
