#!/usr/bin/env python3
import json                             # Need this to format response
import argparse                         # To parse command line arguments
import requests                         # This is needed to talk to the API

# Base url
API_URL = "https://www.deciphergenomics.org/api/"

# Define variables to append to base url to make specific to API endpoints
PATIENT_URL = "patients"
PEOPLE_URL = "people"
VARIANT_URL = "variants"
PHENOTYPE_URL = "phenotypes"

# Use parser to read command line arguments into the script
parser = argparse.ArgumentParser(description="",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("-k", "--configuration", help="API keys for DECIPHER")
parser.add_argument("-c", "--data_for_decipher", help="case data in JSON file")
parser.add_argument("-s", "--submitter", help="DECIPHER submitter ID")

args = parser.parse_args()

# Extract and open JSON file containing API keys
api_file = args.configuration
with open(api_file, 'r') as f:
    datastore = json.load(f)

# Retrieve keys from JSON and set as headers for API call
CLIENT_KEY = datastore["CLIENT_KEY"]
USER_KEY = datastore["USER_KEY"]

headers = {
	"Content-Type" :"application/vnd.api+json",
    "X-Auth-Token-Client": CLIENT_KEY,
    "X-Auth-Token-Account": USER_KEY
}

def submit_data_to_decipher(case, submitter_id):
    """
    Take the json made by the pull_from_opencga.py script and submit the
    information from this json to DECIPHER
        inputs:
            case (json) = the json from the pull_from_opencga.py script
            submitted_id (int) = the ID of the user submitting this data to DECIPHER
        outputs:
            None
    """
    patient_person_id = None

    # Extract patient info from case in case json and format into patient
    # dictionary compatible with DECIPHER API
    proband_id = case['clinical_reference']
    attribute_dict = {
        'contact_account_id': submitter_id,
        'chromosomal_sex': case['sex'],
        'has_aneuploidy': False,
        'clinical_reference': proband_id,
        'has_consent': False
        }
    
    patient_dict = {"data":
        {
        "type": "Patient",
        "attributes": attribute_dict
        }
    }

    patient_json=json.dumps(patient_dict)  # Convert dictionary to JSON

    # Submit patient to DECIPHER via the API
    response = requests.request("POST", API_URL + PATIENT_URL, data=patient_json, headers=headers)
    response_json = json.loads(response.text)

    # Determine if the patient already exists in DECIPHER
    if 'errors' in response_json.keys():
        if response_json['errors'][0]['detail'] == 'Clinical reference must be unique within the project':
            print(
                'Clinical reference must be unique within the project.'
                f'A patient with the local clinical reference number {proband_id}'
                ' already exists in decipher'
                )
            # If the patient exists, do an API "GET" request to get all the existing patients in DECIPHER
            updated_response = requests.request("GET", API_URL + PATIENT_URL, headers=headers)
            updated_response_json = json.loads(updated_response.text)

            # For each patient, check if the clinical reference number matches the current case
            for patient in updated_response_json['data']:
                if patient['attributes']['clinical_reference'] == proband_id:

                    # If the the clinical reference numbers match, request
                    # the API to get the patient's "person ID"
                    person_response = requests.request(
                        "GET", API_URL + PATIENT_URL + '/' + patient['id'] + '/people', headers=headers
                        )
                    print(person_response.text)
                    person_response_json = json.loads(person_response.text)
                    patient_person_id = person_response_json["data"][0]["id"]


    # If the person ID has not been obtained by the previous for loop, aka
    # the patient is not already in DECIPHER, set the patient ID
    if patient_person_id is None:
        patient_person_id = response_json['data'][0]['relationships']['People']['data'][0]['id']

    ## If the case has phenotypes, submit the phenotypes to DECIPHER
    # Define empty list to submit as data input to DECIPHER API
    phenotypes_to_submit = []
    
    # Populate this list from the case json
    if case['phenotype_list']:
        print("found  " + case['phenotype_list'][0])
        for phenotype in case['phenotype_list']:
            phenotypes_to_submit.append({
                "type": "Phenotype",
                "attributes": {
                    "person_id": patient_person_id,
                    "hpo_term_id": phenotype.strip("HP:"),
                    "is_present": True},
            })
        phen_data = {"data": phenotypes_to_submit}
        print(phen_data)

        # Submit phenotypes to DECIPHER
        phenotype_json = json.dumps(phen_data)
        phen_response = requests.request("POST", API_URL + PHENOTYPE_URL, data=phenotype_json, headers=headers)
        print("Querying "  + API_URL + PHENOTYPE_URL)
        print(phen_response.text)
        phen_response_json = json.loads(phen_response.text)
        print(phen_response_json)
        if 'errors' in phen_response_json.keys():
            if phen_response_json['errors'][0]['detail'] == 'Invalid HPO term':
                # If one of the HPO terms is not valid, remove it from the
                # phenotype dictionary and submit the other terms
                # Missing phenotypes can be added manually in the GUI
                invalid_hpo = phen_response_json['errors'][0]['source']["pointer"].rpartition('/')[-1]
                print(invalid_hpo)
                print(phen_data["data"][int(invalid_hpo)])
                del phen_data["data"][int(invalid_hpo)]
                print(phen_data)
                phenotype_json = json.dumps(phen_data)
                phen_response = requests.request("POST", API_URL + PHENOTYPE_URL, data=phenotype_json, headers=headers)
                print(phen_response.text)

    variant_dict_list = []
    for variant in case['variant_list']:

        # Set the values to None so they can be filled later
        heterozygosity = None
        variant_type = None

        # Configure variant type
        if variant["type"] in ["INDEL", "SNV", "INSERTION", "DELETION"]:
            variant_type = "sequence_variant"
        else:
            print ("could not determine variant type for " + variant)

        # Configure heterozygosity
        # Split on '/' or '|' and store as a two-item list
        variant_index = variant["heterozygosity"].replace("|", "/").split("/")
        # If the first and second item in this list are not equal then it is
        # heterozygous, if they are different it is homozygous
        if variant_index[0] != variant_index[1]:
            heterozygosity = "heterozygous"
        elif variant_index[0] == variant_index[1]:
            heterozygosity = "homozygous"

        # Only submit variants if the type and heterozygosity have been 
        # extracted. If both of these variables have been assigned then add the
        # variant to the list of variants to be submitted, in the correct
        # format for submission to DECIPHER
        if variant_type and heterozygosity is not None:
            # The variant index will have two of the same value if the variant
            # is homozygous. The already done list stores the variant indices
            # for variants that have been added to variant_dict_list to ensure
            # that the same variant is not submitted twice
            already_done = []
            for i in variant_index:     
                if i not in already_done:
                    # All non-zero indices indicate that that variant is present
                    # and should be submitted to DECIPHER
                    if i != "0":
                        # If the index is not zero go to that index in the
                        # variant nomenclature and submit that variant
                        variant_dict_list.append(
                                {"data":
                                    {
                                    "type": "Variant",
                                    "attributes": {
                                        "person_id": patient_person_id,
                                        "variant_class": variant_type,
                                        "assembly": "GRCh38",
                                        "chr": variant["variant_id"].split(":")[0],
                                        "start": variant["variant_id"].split(":")[1],
                                        "ref_sequence": variant["variant_id"].split(":")[2],
                                        "alt_sequence": variant["variant_id"].split(":")[3].split(",")[int(i)-1],
                                        "inheritance": "unknown",
                                        "genotype": heterozygosity,
                                        "can_be_public": False,
                                        }
                                    }
                                }
                        )
                already_done.append(i)

    # Submit the variants for this case to DECIPHER
    for variant_dict in variant_dict_list:
        print(variant_dict)
        variant_json_to_submit = json.dumps(variant_dict)
        response = requests.request("POST", API_URL + VARIANT_URL, data=variant_json_to_submit, headers=headers)
        print(response.text)

if args.data_for_decipher and args.submitter:
    data_to_submit = args.data_for_decipher
    with open(data_to_submit, 'r') as f:
        data_to_submit_json = json.load(f)
    submit_data_to_decipher(data_to_submit_json, args.submitter)
