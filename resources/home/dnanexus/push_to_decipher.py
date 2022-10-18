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

# # Get patients
#response = requests.request("GET", api_url + patient_url +'/486637', headers=headers)

# Get people
# response = requests.request("GET", api_url + patient_url + '/' + '482899' + '/' + people_url, headers=headers)

patient_json = args.patient
print(patient_json)

# Need to create a patient first
response = requests.request("POST", api_url + patient_url, data=open(patient_json, 'rb'), headers=headers)

# Add some variants to our new patient
#response = requests.request("POST", api_url + variant_url, data=json.dumps(variant_data), headers=headers)

# Retreive variant for a specific aptient
#response = requests.request("GET", api_url + people_url + '/660113/variants', headers=headers)
print(response.text)
