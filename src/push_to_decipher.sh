#!/bin/bash
set -exo pipefail #if any part goes wrong, job will fail

#dx-download-all-inputs # download inputs from json
dx-download-all-inputs

dx download "$api_keys" -o api_keys.json
dx download "$family_information_json" -o fam.json

python3 /home/dnanexus/push_from_vcf.py --configuration api_keys.json --family fam.json

# if [ -n $patient_json]; then dx download $patient_json -o patient.json
#     python3 /home/dnanexus/push_from_vcf.py --patient patient.json --configuration api_keys.json
#     fi
    
# if [ -n $variant_json]; then dx download $variant_json -o variant.json
#     python3 /home/dnanexus/push_to_decipher.py --variant variant.json --configuration api_keys.json
#     fi
    
#dx download "$variant_json" -o variant.json

