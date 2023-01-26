#!/usr/bin/env python3
import json                             # Need this to format response
import argparse                         # To parse command line arguments
import requests                         # This is needed to talk to the API
from requests.adapters import HTTPAdapter, Retry

# Base url
API_URL = "https://www.deciphergenomics.org/api/"

# Define variables to append to base url to make specific to API endpoints
PATIENT_URL = "patients"
PEOPLE_URL = "people"
VARIANT_URL = "variants"
PHENOTYPE_URL = "phenotypes"

def decipher_api_request(req_type, url, header, data=None):
    '''
    Make a DECIPHER API request.This fucntion includes retries so can attempt
    again if the DECIPHER API is temporarily offline
        inputs:
            req_type (str): the API request type. This function only handles
            "GET" and "POST" as these are the only ones used in the script
            url (str): the API url
            header (dict): the DECIPHER API request header, including client
            key and user key
            data (dict): data to submit via the API. This is optional as it is
            only required for the "POST" request type
        outputs:
            r: the API response
    '''
    s = requests.Session()
    retries = Retry(total=10, backoff_factor=0.5)
    s.mount('https://', HTTPAdapter(max_retries=retries))
    if req_type == "GET":
        r = s.get(url, headers=header)
    if req_type == "POST":
        r = s.post(url, headers=header, data=data)
    return r


def submit_patient_to_decipher(case, headers, submitter_id):
    """
    Take the json made by the pull_from_opencga.py script and submit the
    patient information from this json to DECIPHER. This creates a patient 
    record for the proband or retrieves the patient ID if there is an existing
    patient record
        inputs:
            case (json) = the json from the pull_from_opencga.py script
            submitter_id (int) = the ID of the user submitting data to DECIPHER
        outputs:
            patient_person_id (int) = the Person ID of the patient in DECIPHER
    """
    patient_person_id = None

    # Extract patient info from case json and format into patient dictionary
    # compatible with DECIPHER API
    proband_id = case['clinical_reference']
    attribute_dict = {
        'contact_account_id': submitter_id,
        'chromosomal_sex': case['sex'],
        'has_aneuploidy': False,
        'clinical_reference': proband_id,
        'has_consent': False
        }

    patient_dict = {
        "data": {
                "type": "Patient",
                "attributes": attribute_dict
            }
    }

    patient_json = json.dumps(patient_dict)  # Convert dictionary to JSON

    # Submit patient to DECIPHER via the API
    response = decipher_api_request(
        "POST", API_URL + PATIENT_URL, headers, patient_json
    )
    print(response.text)
    response_json = json.loads(response.text)
    print(response_json)

    # Determine if the patient already exists in DECIPHER
    if 'errors' in response_json.keys():
        if response_json['errors'][0]['detail'] == (
            'Clinical reference must be unique within the project'
        ):
            print(
                'Clinical reference must be unique within the project.'
                'A patient with the local clinical reference number '
                f'{proband_id} already exists in decipher'
                )
            # If the patient exists, do an API "GET" request to get all the
            # existing patients in DECIPHER
            updated_response = decipher_api_request(
                "GET", API_URL + PATIENT_URL, headers
                )
            updated_response_json = json.loads(updated_response.text)

            # For each patient, check if the clinical reference number matches
            # the current case
            for patient in updated_response_json['data']:
                if patient['attributes']['clinical_reference'] == proband_id:

                    # If the the clinical reference numbers match, request
                    # the API to get the patient's "person ID"
                    person_response = decipher_api_request(
                        "GET",
                        API_URL + PATIENT_URL + '/' + patient['id'] + '/people',
                        headers
                    )
                    print(person_response.text)
                    person_response_json = json.loads(person_response.text)
                    patient_person_id = person_response_json["data"][0]["id"]

    # If the person ID has not been obtained by the previous for loop, aka
    # the patient is not already in DECIPHER, set the patient ID
    if not patient_person_id:
        patient_person_id = response_json['data'][0]['relationships']['People']['data'][0]['id']

    return patient_person_id


def submit_phenotypes_to_decipher(case, headers, patient_person_id):
    """
    Take the json made by the pull_from_opencga.py script and submit the
    phenotype information from this json to DECIPHER.
        inputs:
            case (json) = the json from the pull_from_opencga.py script
            patient_person_id (int) = the Person ID of the proband in DECIPHER
        outputs:
            None
    """
    # If the case has phenotypes, submit the phenotypes to DECIPHER
    # Define empty list to submit as data input to DECIPHER API
    phenotypes_to_submit = []

    # Populate this list from the case json
    for phenotype in case.get('phenotype_list', []):
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
    phen_response = decipher_api_request(
        "POST", API_URL + PHENOTYPE_URL, headers, phenotype_json
    )
    print("Querying " + API_URL + PHENOTYPE_URL)
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
            phen_response = decipher_api_request(
                "POST", API_URL + PHENOTYPE_URL, headers, phenotype_json
            )
            print(phen_response.text)


def calculate_variant_type(variant):
    '''
    Converts variant type into variant types that are compatible with DECIPHER
        inputs:
            variant: the variant from the OpenCGA case json
        outputs:
            variant_type: the variant type in format compatible with DECIPHER
    '''
    if variant["type"] in ["INDEL", "SNV", "INSERTION", "DELETION"]:
        variant_type = "sequence_variant"
    else:
        print(
            "The variant type is " + variant["type"] + ". This is cannot be "
            "submitted to DECIPHER by eggd_pandora, as it currently only "
            "submits sequence variants"
            )
        variant_type = None
    return variant_type
    

def calculate_zygosity(variant):
    '''
    Work out the zygosity from the OpenCGA case json for the case['variant']
        input:
            a variant
        output:
            zygosity (str): the zygosity of the variant
    '''
    # Split on '/' or '|' and store as a two-item list
    variant_index = variant["heterozygosity"].replace("|", "/").split("/")
    # If the first and second item in this list are not equal then it is
    # heterozygous, if they are different it is homozygous
    if variant_index[0] != variant_index[1]:
        zygosity = "heterozygous"
    elif variant_index[0] == variant_index[1]:
        zygosity = "homozygous"
    else:
        print(f"Could not determine zygosity from the input {variant_index}")
        zygosity = None
    return zygosity


def format_variant_json_for_decipher(variant, person_id, zygosity, var_type):
    '''
    Formats the variant info into a DECIPHER-compatible dictionary
        inputs:
            variant: the variant from the OpenCGA case json
            patient_person_id: the person ID of the patient record in DECIPHER
            to which these variants should be added.
            zygosity: the zygosity of the variant
            var_type: the variant type
        outputs:
            variant_dict: a variant dictonary which is in the format needed for
            submission to the DECIPHER API

    '''
    # Split the variant zygosity on '/' or '|' and store as a two-item list
    variant_index = variant["heterozygosity"].replace("|", "/").split("/")

    # The variant index will have two of the same value if the variant
    # is homozygous. Using set(variant_index) removes duplicate variant
    # indices ensuring that homozygous variants are not submitted twice
    variant_dict_list = []

    print(set(variant_index))

    # If the zygosity were 0/0 this should return None
    if set(variant_index) == {"0"}:
        variant_dict_list = None

    for i in set(variant_index):
        # All non-zero indices indicate that that variant exists
        # and should be submitted to DECIPHER
        if i != "0":
            # If the index is not zero go to that index in the
            # variant nomenclature and submit that variant
            variant_dict = {"data": {
                    "type": "Variant",
                    "attributes": {
                        "person_id": person_id,
                        "variant_class": var_type,
                        "assembly": "GRCh38",
                        "chr": variant["variant_id"].split(":")[0],
                        "start": variant["variant_id"].split(":")[1],
                        "ref_sequence": variant["variant_id"].split(":")[2],
                        "alt_sequence": variant["variant_id"].split(":")[3].split(",")[int(i)-1],
                        "inheritance": "unknown",
                        "genotype": zygosity,
                        "can_be_public": False,
                    }
                }}
            variant_dict_list.append(variant_dict)

    return variant_dict_list


def submit_variants_to_decipher(case, headers, patient_person_id):
    """
    Take the json made by the pull_from_opencga.py script and submit the
    variant information from this json to DECIPHER.
        inputs:
            case (json) = the json from the pull_from_opencga.py script
            patient_person_id (int) = the Person ID of the proband in DECIPHER
        outputs:
            None
    """
    for variant in case['variant_list']:
        variant_type = calculate_variant_type(variant)
        zygosity = calculate_zygosity(variant)

        # Submit variants only if variant type and zygosity have been worked
        # out correctly
        if variant_type and zygosity is not None:
            variant_dict_list = format_variant_json_for_decipher(variant, patient_person_id, zygosity, variant_type)
            for variant_dict in variant_dict_list:
                variant_json_to_submit = json.dumps(variant_dict)
                response = decipher_api_request(
                    "POST", API_URL + VARIANT_URL, headers, variant_json_to_submit
                )
                print(response.text)


if __name__ == "__main__":
    # Use parser to read command line arguments into the script
    parser = argparse.ArgumentParser(
                                    description="",
                                    formatter_class=(
                                    argparse.ArgumentDefaultsHelpFormatter
                                    )
                                )

    parser.add_argument("-k", "--configuration", help="API keys for DECIPHER")
    parser.add_argument("-c", "--data_for_decipher", help="case data in JSON file")
    parser.add_argument("-s", "--submitter", help="DECIPHER submitter ID")

    args = parser.parse_args()

    # Extract and open JSON file containing API keys
    decipher_api_keys_file = args.configuration
    with open(decipher_api_keys_file, 'r', encoding='utf-8') as f:
        decipher_api_keys = json.load(f)

    # Retrieve keys from JSON and set as headers for API call
    CLIENT_KEY = decipher_api_keys["CLIENT_KEY"]
    USER_KEY = decipher_api_keys["USER_KEY"]

    decipher_api_request_headers = {
        "Content-Type": "application/vnd.api+json",
        "X-Auth-Token-Client": CLIENT_KEY,
        "X-Auth-Token-Account": USER_KEY
    }
    data_to_submit = args.data_for_decipher
    with open(data_to_submit, 'r', encoding='utf-8') as f:
        data_to_submit_json = json.load(f)
    decipher_person_id = submit_patient_to_decipher(
        data_to_submit_json, decipher_api_request_headers, args.submitter
        )
    submit_phenotypes_to_decipher(
        data_to_submit_json, decipher_api_request_headers, decipher_person_id
        )
    submit_variants_to_decipher(
        data_to_submit_json, decipher_api_request_headers, decipher_person_id
        )
