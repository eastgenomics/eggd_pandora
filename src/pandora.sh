#!/bin/bash
set -exo pipefail #if any part goes wrong, job will fail
pip install pyopencga
dx-download-all-inputs

dx download "$decipher_api_keys" -o decipher_api_keys.json
dx download "$opencga_config" -o opencga_login

python3 /home/dnanexus/pull_from_opencga.py --configuration opencga_login --case $opencga_case_id --study $opencga_study_name
python3 /home/dnanexus/push_to_decipher.py --configuration decipher_api_keys.json --data_for_decipher case_phenotype_and_variant_data.json --submitter $decipher_submitter_id
