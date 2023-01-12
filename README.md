# eggd_pandora

## What does this app do?
When given a case in OpenCGA this app accesses the primary interpretation for the case and submits the variants that have been interpreted for the proband to the DECIPHER database. 

## What inputs are required for this app to run?
* `--decipher_api_keys`: (file) DNAnexus link to JSON file with client and user keys to access the API for the DECIPHER project to which the variants should be submitted
* `--opencga_config`: (file) DNAnexus link to JSON file with the user and password for OpenCGA
* `--opencga_case_id`: (string) the case ID on OpenCGA for the case that is to be submitted to DECIPHER
* `--opencga_study_name`: (string) the study where the case is found
* `--decipher_submitter_id`: (int) the DECIPHER account ID of the submitter

## How does this app work?
This app runs the script pandora.sh. which runs pull_from_opencga.py, which is a python script that extracts the necessary information for each case to be submitted to DECIPHER and outputs it in a JSON called case_phenotype_and_variant_data.json, which is in the following format:
```
    case_dict = {
        'sex': sex,
        'clinical_reference': opencga_proband_id,
        'phenotype_list': phenotype_list,
        'variant_list': variant_list
    }
```
The pandora.sh script then inputs this JSON to the push_to_decipher.py script which reformats this information and submits it to DECIPHER

## What does this app output?
This app creates a DECIPHER patient record for a case in OpenCGA and adds HPO phenotype terms and intepreted variants. The eggd_pandora app will create a proband patient record in DECIPHER if needed, or add the variants to an existing patient.