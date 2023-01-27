#!/bin/bash
set -exo pipefail #if any part goes wrong, job will fail
pip install pyopencga
pip install pytest

dx-download-all-inputs

python3 /home/dnanexus/pull_from_opencga.py \
    --configuration /home/dnanexus/in/opencga_config/*.json \
    --case $opencga_case_id \
    --study $opencga_study_name

python3 /home/dnanexus/push_to_decipher.py \
    --configuration /home/dnanexus/in/decipher_api_keys/*.json \
    --data_for_decipher case_phenotype_and_variant_data.json \
    --submitter $decipher_submitter_id

DECIPHER_URL=$(cat decipher_url.txt)

dx-jobutil-add-output link_to_patient_in_decipher "$DECIPHER_URL" --class=string