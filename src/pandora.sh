#!/bin/bash
set -exo pipefail #if any part goes wrong, job will fail
pip install pytest
dx-download-all-inputs

if [ "$running_mode" = "decipher" ]
then
    pip install pyopencga
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

elif [ "$running_mode" = "clinvar" ]
then
    pip install pandas
    python3 /home/dnanexus/pull_from_csv.py \
        --variant_csv /home/dnanexus/in/variant_csv/*.csv

    for json in $(ls /home/dnanexus/*_clinvar_data.json)
    do
        python3 /home/dnanexus/push_to_clinvar.py \
        --clinvar_api_key /home/dnanexus/in/clinvar_api_key/*.txt \
        --clinvar_json $json \
        --clinvar_testing $clinvar_testing
    done
    mkdir -p /home/dnanexus/out/submission_id
    mv submission_ids.txt /home/dnanexus/out/submission_id

    dx-upload-all-outputs
elif [ "$running_mode" = "get_clinvar_accession" ]
then
    python3 /home/dnanexus/get_clinvar_accession.py \
        --submission_file /home/dnanexus/in/submission_ids_file/*.tsv \
        --clinvar_api_key /home/dnanexus/in/clinvar_api_key/*.txt
    mkdir /home/dnanexus/out/accession_id
    mv accession_ids.txt /home/dnanexus/out/accession_id
else
    echo Running mode $running_mode is not valid please choose one of the following:
    echo 'clinvar', 'decipher', 'get_clinvar_accession'
    exit 1
fi





