#!/usr/bin/env python3
import os
import requests                         # This is needed to talk to the API
import json                             # Need this to format response

with open('/home/katherine/push_to_decipher/SAP-56130-1-payload.json') as input_fam_json:
    fam_json = json.load(input_fam_json)

print(fam_json["interpretation_request_data"]["json_request"]["pedigree"]["members"])

for member in fam_json["interpretation_request_data"]["json_request"]["pedigree"]["members"]:
    # Create patient from proband
    if member.get('isProband') is True:
        print(member['participantId'])
        proband_id = member['paticipantId']