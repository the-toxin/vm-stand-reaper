#!/usr/bin/env bash

set -uo pipefail nounset

export YC_TOKEN=$DEV_YC_TOKEN

cd ./infra/terragrunt/dev/

echo "INFO: destroy of all DEV stands"
for s in $(ls -d */); do
    cd ${s%%/};
    terragrunt run --all destroy --non-interactive;
    cd ../;
done
echo "INFO: destroy all DEV stands finished successfully"
