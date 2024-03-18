import json 
import requests
from requests.adapters import HTTPAdapter, Retry
import argparse
import os.path

def make_headers(api_key: str):
    '''
    Construct headers using the contents of a file containing the API key
    '''
    if not isinstance(api_key, str):
        raise TypeError(
            'Value given as ClinVar API key is not a string'
        )
    else:
        headers = {
            "SP-API-KEY": api_key,
            "Content-type": "application/json"
        }
    return headers

def select_api_url(testing):
    '''
    Select which API URL to use depending on if this is a test run or if
    variants are planned to be submitted to ClinVar
    '''
    if testing in ["True", True, "true"]:
        api_url = "https://submit.ncbi.nlm.nih.gov/apitest/v1/submissions"
        print(
            f"Running in test mode, using {api_url}"
        )
    elif testing in ["False", False, "false"]:
        api_url = "https://submit.ncbi.nlm.nih.gov/api/v1/submissions/"
        print(
            f"Running in live mode, using {api_url}"
        )
    else:
        raise RuntimeError(
            f"Value for testing {testing} neither True nor False. Please "
            "specify whether this is a test run or not."
        )
    return api_url

def clinvar_api_request(url, header, data):
    '''
    Make request to the ClinVar API endpoint specified.
    Inputs:
        url (str): API endpoint URL
        header (dict): headers for API call
        data (dict): clinvar data to submit
    
    Returns:
        response: API response object
    '''
    clinvar_data = {
        "actions": [{
            "type": "AddData",
            "targetDb": "clinvar",
            "data": {"content": data}
        }]
    }

    print("JSON to submit:")
    print(json.dumps(clinvar_data, indent='⠀⠀'))

    s = requests.Session()
    retries = Retry(total=10, backoff_factor=0.5)
    s.mount('https://', HTTPAdapter(max_retries=retries))
    response = s.post(url, data=json.dumps(clinvar_data), headers=header)
    return response

def write_response_to_file(local_id, response):
    '''
    Write the response of the ClinVar API submission to a file. This script
    will be ran multiple times per sample if there is more than one variant for
    submission to ClinVar, so we need to check if the submission response file
    already exists + make it if it does not.
    Inputs:
        local_id (str): local ID for the variant
        response (dict): response json from the ClinVar API, converted to dict
    Outputs:
        None, modifies/creates file for upload to DNAnexus
    '''
    if not os.path.exists('submission_ids.txt'):
        with open('submission_ids.txt', 'a', encoding='utf-8') as f:
            f.write(
                'Local_ID\tClinVar_Submission_ID\n'
            )

    if 'id' in response:
        # If the submission response has an 'id' key then submission has been
        # successful
        submission_id = response['id']
        with open('submission_ids.txt', 'a', encoding='utf-8') as f:
            f.write(f'{local_id}\t{submission_id}\n')
    else:
        with open('submission_ids.txt', 'a', encoding='utf-8') as f:
            f.write(f'{local_id}\tSubmission_error_check_logs\n')

def main():
    '''
    Script entry point
    '''
    parser = argparse.ArgumentParser(
                            description="",
                            formatter_class=(
                                argparse.ArgumentDefaultsHelpFormatter
                                )
                        )

    parser.add_argument('--clinvar_json')
    parser.add_argument('--clinvar_api_key')
    parser.add_argument('--clinvar_testing')
    args = parser.parse_args()

    with open(args.clinvar_api_key) as f:
        api_key = f.readlines()[0].strip()

    with open(args.clinvar_json) as f:
        data = json.load(f)

    api_url = select_api_url(args.clinvar_testing)

    headers = make_headers(api_key)

    response = clinvar_api_request(api_url, headers, data)
    response_dict = response.json()

    # print to logs, use braille blank character so DNAnexus won't strip
    # whitespace
    print(json.dumps(response_dict, indent='⠀⠀'))

    local_id = data["clinvarSubmission"][0]["localID"]

    write_response_to_file(local_id, response_dict)

if __name__ == "__main__":
    main()
