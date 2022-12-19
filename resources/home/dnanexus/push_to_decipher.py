#!/usr/bin/env python3
import requests                         # This is needed to talk to the API
import json                             # Need this to format response
import argparse                         # To parse command line arguments
#from config import CLIENT_KEY, USER_KEY # API keys for TCA project in DECIPHER

# Base url
api_url = "https://www.deciphergenomics.org/api/"

# Append to base url to make specific to API endpoint for patients or variants
patient_url = "patients"
people_url = "people"
variant_url = "variants"


parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("-p", "--patient", help="patient data in JSON file")
parser.add_argument("-v", "--variant", help="variant data in JSON file")
parser.add_argument("-k", "--configuration", help="variant data in JSON file")

args = parser.parse_args()
print(args)

# Extract and open JSON file containing API keys
api_file = args.configuration
with open(api_file, 'r') as f:
    datastore = json.load(f)

# Retrieve keys from JSON 
CLIENT_KEY = datastore["CLIENT_KEY"]
USER_KEY = datastore["USER_KEY"]

headers = {
	"Content-Type" :"application/vnd.api+json",
    "X-Auth-Token-Client": CLIENT_KEY,
    "X-Auth-Token-Account": USER_KEY
}

def create_family_in_decipher():
    '''
    Use a JSON with a patient and their family and create corresponding records
    in DECIPHER 
    '''
    family_information_json = args.family
    with open(family_information_json, 'r') as f:
        fam_json = json.load(f)


    #print(fam_json["interpretation_request_data"]["json_request"]["pedigree"]["members"])

    for member in fam_json["interpretation_request_data"]["json_request"]["pedigree"]["members"]:
        print(member['participantId'])
        # Create patient from proband
        if member.get('isProband') is True:
            print(member['participantId'])
            proband_id = member['participantId']
            if member.get('personKaryotypicSex') == 'XY':
                proband_sex = "46_xy"
            elif member.get('personKaryotypicSex') == 'XX':
                proband_sex = "46_xx"
            elif member.get('sex') == 'FEMALE':
                proband_sex = "unknown"
                proband_phenotypic_sex = "female"
            elif member.get('sex') == 'MALE':
                proband_sex = "unknown"
                proband_phenotypic_sex = "male"
            else:
                print("Issue determining proband sex from input JSON")
            print(proband_sex)

    # Find affected status of mother 
    for member in fam_json["interpretation_request_data"]["json_request"]["pedigree"]["members"]:
        if member.get('additionalInformation')['relation_to_proband'] == "Mother":
            if member.get('affectionStatus') == "AFFECTED":
                mother_affected_status = "affected"
            elif member.get('affectionStatus') == "UNAFFECTED":
                mother_affected_status = "affected"
            elif member.get('affectionStatus') == "UNCERTAIN":
                mother_affected_status = "unknown"
            else:
                print("Could not detemine affected status of mother")
            mother_sample_id = member.get('samples')[0]['sampleId']

        if member.get('additionalInformation')['relation_to_proband']== "Father":
            if member.get('affectionStatus') == "AFFECTED":
                father_affected_status = "affected"
            elif member.get('affectionStatus') == "UNAFFECTED":
                father_affected_status = "affected"
            elif member.get('affectionStatus') == "UNCERTAIN":
                father_affected_status = "unknown"
            else:
                print("Could not detemine affected status of father")
            father_sample_id = member.get('samples')[0]['sampleId']

    # Make a patient json
    attribute_dict = {'contact_account_id': 4812, 'chromosomal_sex': proband_sex, 'has_aneuploidy': False, 'clinical_reference': proband_id, 'has_consent': False}
    patient_dict = {"data":
        {
        "type": "Patient",
        "attributes": attribute_dict
        }
    }
    patient_json=json.dumps(patient_dict)

    response = requests.request("POST", api_url + patient_url, data=patient_json, headers=headers)
    response_json = json.loads(response.text)
    print(response_json)
    patient_id = response_json['data'][0]['id']
    create_family_in_decipher.patient_person_id = response_json['data'][0]['relationships']['People']['data'][0]['id']
    # Add parents
    # Mother is created first, so indexed at [1]
    mother_id = response_json['data'][0]['relationships']['People']['data'][1]['id']
    # Father is created second, so indexed at [2]
    father_id = response_json['data'][0]['relationships']['People']['data'][2]['id']

    # Make a parent jsons
    mother_dict = {"data":
        {
        "type": "Person",
        "id": mother_id,
        "attributes": {
            "relation_status": mother_affected_status
        }
        }
    }
    father_dict = {"data":
        {
        "type": "Person",
        "id": father_id,
        "attributes": {
            "relation_status": father_affected_status
        }
        }
    }
    # Convert to JSON
    mother_json = json.dumps(mother_dict)
    father_json = json.dumps(father_dict)

    response = requests.request("PATCH", api_url + people_url + '/' + str(mother_id), data=mother_json, headers=headers)
    print('Querying.... ' + api_url + people_url + mother_id)
    print(response.text)
    response = requests.request("PATCH", api_url + people_url + '/' + str(father_id), data=father_json, headers=headers)
    print(response.text)

def submit_variants_from_opencga(person_id):
    variant_json = args.variant
    print(variant_json)
    variant_dict = {"data":
    {
    "type": "Variant",
    "attributes": {
        "person_id": person_id,
        "variant_class": "sequence_variant",
        "assembly": "GRCh38",
        "chr": variant_json["variant_id"].split(":")[0],
        "start": variant_json["variant_id"].split(":")[1],
        "ref_sequence": variant_json["variant_id"].split(":")[2],
        "alt_sequence": variant_json["variant_id"].split(":")[3],
        "inheritance": "unknown",
        "genotype": "heterozygous",
        "can_be_public": False,
        }
    }
}
    variant_json_to_submit = json.dumps(variant_dict)
    response = requests.request("POST", api_url + variant_url, data=variant_json_to_submit, headers=headers)
    print(response)

if args.family and args.variant:
    create_family_in_decipher()
    patient_person_id = create_family_in_decipher.patient_person_id
    submit_variants_from_opencga(patient_person_id)

# # Get patients
#response = requests.request("GET", api_url + patient_url +'/486637', headers=headers)

# Get people
# response = requests.request("GET", api_url + patient_url + '/' + '482899' + '/' + people_url, headers=headers)

# patient_json = args.patient
# print(patient_json)

# variant_json = args.variant
# print(variant_json)

# # Need to create a patient first
# response = requests.request("POST", api_url + patient_url, data=open(patient_json, 'rb'), headers=headers)

# # Add some variants to our new patient
# #response = requests.request("POST", api_url + variant_url, data=json.dumps(variant_data), headers=headers)

# # Retreive variant for a specific aptient
# #response = requests.request("GET", api_url + people_url + '/660113/variants', headers=headers)
# print(response.text)
