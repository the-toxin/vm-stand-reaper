#!/usr/bin/env bash

set -euo pipefail

export YC_TOKEN=$DEV_YC_TOKEN

cd ./infra/terragrunt/dev/

echo "INFO: deploy of all DEV stands"
for s in $(ls -d */); do
    cd ${s%%/};
    terragrunt run --all apply --non-interactive;
    cd ../;
done
echo "INFO: deploy all DEV stands finished successfully"
