import os
import json
import argparse
import time
import requests
import pandas as pd
from push_to_clinvar import make_headers, select_api_url


def submission_status_check(submission_id, headers, api_url):
    '''
    Queries ClinVar API about a submission ID to obtain more details about its
    submission record.
    Inputs:
        submission_id:  the generated submission id from ClinVar when a
        submission has been posted to their API
        headers: the required API url
    Outputs:
        status_response: the API response
    '''

    url = os.path.join(api_url, submission_id, "actions")
    response = requests.get(url, headers=headers)
    response_content = response.content.decode("UTF-8")
    for k, v in response.headers.items():
        print(f"{k}: {v}")
    print(response_content)
    if response.status_code not in [200]:
        raise RuntimeError(
            "Status check failed:\n" + str(headers) + "\n" + url
            + "\n" + response_content
        )

    status_response = json.loads(response_content)

    # Load summary file
    action = status_response["actions"][0]
    status = action["status"]
    print(f"Submission {submission_id} has status {status}")

    responses = action["responses"]
    if len(responses) == 0:
        print("Status 'responses' field had no items, check back later")
    else:
        print(
            "Status response had a response, attempting to "
            "retrieve any files listed"
        )
        try:
            f_url = responses[0]["files"][0]["url"]
        except (KeyError, IndexError) as error:
            f_url = None
            print(
                f"Error retrieving files: {error}.\n No API url for summary"
                "file found. Cannot query API for summary file based on "
                f"response {responses}"
            )

        if f_url is not None:
            print("GET " + f_url)
            f_response = requests.get(f_url, headers=headers)
            f_response_content = f_response.content.decode("UTF-8")
            if f_response.status_code not in [200]:
                raise RuntimeError(
                    "Status check summary file fetch failed:"
                    f"{f_response_content}"
                )
            file_content = json.loads(f_response_content)
            status_response = file_content

    return status_response


def get_accession_id(api_response):
    '''
    Check if clinvar accession ID is present in response dict, if not report
    this to user by printing to terminal
    Inputs:
        api_response (dict): dict of reponse of API to query about submission
        ID of variant
    Outputs:
        accession: ClinVar accession ID, or None, if no accession ID found
    '''
    print(f"response is {api_response}")

    try:
        accession = api_response["submissions"][0]["identifiers"][
            "clinvarAccession"
        ]
    except KeyError:
        accession = None
        print(
            "clinvarAccession field not found in response json. Submission may"
            " not have been processed yet. Please check back again or check "
            f"API response for more information\n {api_response}"
        )

    return accession


def write_accession_id_to_file(local_id, accession):
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
    if not os.path.exists('accession_ids.txt'):
        with open('accession_ids.txt', 'a', encoding='utf-8') as f:
            f.write(
                'Local_ID\tClinVar_Accession_ID\n'
            )

    with open('accession_ids.txt', 'a', encoding='utf-8') as f:
        f.write(f'{local_id}\t{accession}\n')


def run_submission_status_check(local_id,
                                submission_id,
                                headers,
                                api_url):
    '''
    Run the submission status check, if accession_id is returned, quit function
    if not, wait 5 mins, run again
    Function will quit after 12 attempts = an hour of querying the API
    '''
    print(f"Querying {api_url} with {submission_id}")
    response = submission_status_check(submission_id, headers, api_url)
    accession_id = get_accession_id(response)
    counter = 0
    if accession_id is not None:
        print(
            f"ClinVar accession ID found to be {accession_id}. \nWriting to "
            "file..."
        )
        write_accession_id_to_file(local_id, accession_id)

    else:
        while counter < 12 and accession_id is None:
            time.sleep(300)
            response = submission_status_check(submission_id, headers, api_url)
            counter += 1
            accession_id = get_accession_id(response)
        write_accession_id_to_file(local_id, str(accession_id))


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

    parser.add_argument('--submission_file')
    parser.add_argument('--submission_id')
    parser.add_argument('--local_id')
    parser.add_argument('--clinvar_api_key')
    parser.add_argument('--clinvar_testing')
    args = parser.parse_args()

    with open(args.clinvar_api_key) as f:
        api_key = f.readlines()[0].strip()

    headers = make_headers(api_key)
    api_url = select_api_url(args.clinvar_testing)

    if args.clinvar_testing in [True, 'true', 'True', 'TRUE']:
        print(
            "ClinVar testing set to true. As this run of eggd_pandora used the"
            "test endpoint, so no ClinVar accession IDs will be generated. "
            "Exiting get_clinvar_accession.py script..."     
        )
        exit(0)

    if args.submission_file:
        with open(args.submission_file) as f:
            df = pd.read_csv(f, delim_whitespace=True)

        print(df)

        for index, row in df.iterrows():
            run_submission_status_check(
                row["Local_ID"],
                row["ClinVar_Submission_ID"],
                headers,
                api_url
            )

    if args.submission_id:
        run_submission_status_check(
            args.local_id,
            args.submission_id,
            headers,
            api_url
        )


if __name__ == "__main__":
    main()
