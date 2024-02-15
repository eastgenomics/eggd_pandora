import json 
import requests
from requests.adapters import HTTPAdapter, Retry
import argparse
import os.path

def make_headers(api_key):
    '''
    Construct headers using the contents of a file containing the API key
    '''
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
            f"Running in test mode, submitting to {api_url}"
        )
    elif testing in ["False", False, "false"]:
        api_url = "not_here_yet_for_safety_reasons"
        print(
            f"Running in live mode, submitting to {api_url}"
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
    print(json.dumps(clinvar_data, indent=4))

    s = requests.Session()
    retries = Retry(total=10, backoff_factor=0.5)
    s.mount('https://', HTTPAdapter(max_retries=retries))
    response = s.post(url, data=json.dumps(clinvar_data), headers=header)
    return response

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
    submission = response.json()
    print(json.dumps(submission), indent='⠀⠀')

    local_id = data["clinvarSubmission"][0]["localID"]

    if not os.path.exists('submission_ids.txt'):
        with open('submission_ids.txt', 'a', encoding='utf-8') as f:
            f.write(
                'Local_ID\tClinVar_Submission_ID\n'
            )

    if 'id' in submission:
        submission_id = submission['id']
        with open('submission_ids.txt', 'a', encoding='utf-8') as f:
            f.write(f'{local_id}\t{submission_id}\n')
    else:
        with open('submission_ids.txt', 'a', encoding='utf-8') as f:
            f.write(f'{local_id}\tSubmission_error_check_logs\n')

if __name__ == "__main__":
    main()
