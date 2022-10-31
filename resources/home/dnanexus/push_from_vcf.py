#!/usr/bin/env python3
import vcf
import requests                         # This is needed to talk to the API
import json                             # Need this to format response
import argparse

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
parser.add_argument("-f", "--family", help="family data in JSON file")
parser.add_argument("-k", "--configuration", help="variant data in JSON file")
parser.add_argument("--patient_vcf_EH", help="patient EH vcf")

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

patient_vcf_EH = args.patient_vcf_EH

def submit_patient_vcf():
    '''
    Add variants from a vcf to an existing patient in DECIPHER
    '''
    patient_vcf = vcf.Reader(open(patient_vcf_EH))
    patient_id = patient_vcf.samples
    patient_id = patient_id[0]
    #variant_list = []
    for record in patient_vcf:
        print(record)
        #variant_list.append([record.CHROM, record.POS, record.REF, record.ALT])
        print(record.heterozygosity)
        if record.heterozygosity == 0.5:
            heterozygosity = "heterozygous"
        elif record.heterozygosity == 1:
            heterozygosity = "homozygous"
        elif record.heterozygosity == 0.0:
            print("The variant " + str(record) + " is not present in the person")
            continue
        if 'Y' in str(record.CHROM):
            heterozygosity = "hemizygous"

        if ',' in str(record.ALT):
            print ("Cannot handle multiple variants in single line of .vcf")
            continue

        if 'STR' in str(record.ALT):
            repeats = str(record.ALT).replace("[<STR", "").replace(">]", "")
            variant_dict = {"data":
                {
                "type": "Variant",
                "attributes": {
                    "person_id": 681378,
                    "variant_class": "duplication",
                    "assembly": "GRCh38",
                    "chr": str(record.CHROM).replace("chr", ""),
                    "start": str(record.POS),
                    "end": str(int(record.POS) + int(repeats)),
                    "inheritance": "unknown",
                    "genotype": heterozygosity,
                    "can_be_public": False,
                    }
                }
            }
            print(variant_dict)
            variant_json = json.dumps(variant_dict)
            response = requests.request("POST", api_url + variant_url, data=variant_json, headers=headers)
        # if 'A' or 'G' or 'C' or 'T' in str(record.ALT):     
        #     variant_dict = {"data":
        #         {
        #         "type": "Variant",
        #         "attributes": {
        #             "person_id": 681378,
        #             "variant_class": "sequence_variant",
        #             "assembly": "GRCh38",
        #             "chr": str(record.CHROM).replace("chr", ""),
        #             "start": str(record.POS),
        #             "ref_sequence": str(record.REF),
        #             "alt_sequence": str(record.ALT),
        #             "inheritance": "unknown",
        #             "genotype": heterozygosity,
        #             "can_be_public": False,
        #             }
        #         }
        #     }
        #     variant_json = json.dumps(variant_dict)
        #     response = requests.request("POST", api_url + variant_url, data=variant_json, headers=headers)
        print(response.text)

submit_patient_vcf()

# Make a relative json
# relation_dict = {"data":
#     {
#       "type": "Person",
#       "attributes": {
#         "patient_id": patient_id,
#         "relation": relation,
#         "relation_status": relation_affected_status
#       }
#     }
#   }

# relation_json = json.dumps(relation_dict)

# response = requests.request("POST", api_url + people_url, data=relation_json, headers=headers)
# print(response.text)
