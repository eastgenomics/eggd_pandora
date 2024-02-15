# eggd_pandora

## What does this app do?
When given a case in OpenCGA this app accesses the primary interpretation for the case and submits the variants that have been interpreted for the proband to the DECIPHER database. 

## What inputs are required for this app to run?
* `--running_mode`: (str) mode that eggd_pandora should run in:
    * "decipher" - pull from OpenCGA and push to DECIPHER
    * "clinvar" - take in a variant csv and submit all the variants in it to ClinVar
### DECIPHER
* `--decipher_api_keys`: (file) DNAnexus link to JSON file containing the client key and user key to access the API for the DECIPHER project to which the variants should be submitted
* `--opencga_config`: (file) DNAnexus link to JSON file containing the user and password for OpenCGA
* `--opencga_case_id`: (string) the case ID on OpenCGA for the case that is to be submitted to DECIPHER
* `--opencga_study_name`: (string) the name of the OpenCGA study containing the case that is to be submitted to DECIPHER
* `--decipher_submitter_id`: (int) the DECIPHER account ID of the submitter
### ClinVar
* `--variant_csv`: (file) Variant .csv file with data that should be converted to a JSON
* `--clinvar_api_key`: (file) File containing ClinVar API key
* `--clinvar_json`: (file) JSON to be submit to ClinVar
* `--clinvar_testing`: (bool) whether or not to use the ClinVar test endpoint (True) or live endpoint (False)


## How does this app work?
This app runs the script pandora.sh which can run both DECIPHER and ClinVar variant submissions.
In "decipher" running mode, pandora.sh will run the pull_from_opencga.py, which is a python script that extracts the necessary information for the case to be submitted to DECIPHER and outputs it in a JSON called case_phenotype_and_variant_data.json. This JSON is then passed to the push_to_decipher.py script which reformats this information and submits it to DECIPHER
In "clinvar" running mode, pandora.sh will run the pull_from_csv.py script to extract the necessary information for submission to ClinVar from a csv of variant data and export a JSON for each variant. These variant JSONs are then passed to the push_to_clinvar.py script and the variant data is submitted to ClinVar.

## What does this app output?
In DECIPHER mode:
This app creates a DECIPHER patient record for a case in OpenCGA and adds HPO phenotype terms and intepreted variants. The eggd_pandora app will create a new proband patient record in DECIPHER if the patient does not already exist, or add the variants to an existing patient. The app outputs a link to the new or updated patient record.
In ClinVar mode:
The app outputs the JSON files used to submit the variants to ClinVar, and a tsv with the local ID and the ClinVar submission ID for each variant

## This app was made by East GLH