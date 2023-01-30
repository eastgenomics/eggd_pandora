#!/bin/bash
set -exo pipefail #if any part goes wrong, job will fail

# Install packages. This script uses pyopencga version 2.9.4, which is matches the server version.
export PATH=$PATH:/home/dnanexus/.local/bin  # pip installs some packages here, add to path
sudo -H python3 -m pip install --no-index --no-deps packages/*

dx-download-all-inputs

# Run pull_from_opencga.py which extracts case data from OpenCGA 
python3 /home/dnanexus/pull_from_opencga.py \
    --configuration /home/dnanexus/in/opencga_config/*.json \
    --case $opencga_case_id \
    --study $opencga_study_name

# Run push_to_decipher.py which pushes case data to DECIHER
python3 /home/dnanexus/push_to_decipher.py \
    --configuration /home/dnanexus/in/decipher_api_keys/*.json \
    --data_for_decipher case_phenotype_and_variant_data.json \
    --submitter $decipher_submitter_id

# Extract URL to case patient record in DECIPHER and upload as app output
DECIPHER_URL=$(cat decipher_url.txt)
dx-jobutil-add-output link_to_patient_in_decipher "$DECIPHER_URL" --class=string