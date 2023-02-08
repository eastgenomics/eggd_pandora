#!/usr/bin/env python3
import json
import argparse
from pyopencga.opencga_config import ClientConfiguration
from pyopencga.opencga_client import OpencgaClient


def extract_case_from_opencga(case, study, oc):
    '''
    Retreives the case information from the Analysis - Clinical client of the
    OpenCGA API
        inputs:
            case (str): the case name in OpenCGA
            study (str): the study that contains the case
            oc: an instance of the OpenCGA client, logged in with a user and
            password
        outputs:
            clinical_anlaysis: a dictionary of case information returned from
            the OpenCGA API
    '''
    # Find this case from the 
    clinical_analysis = oc.clinical.search(study=study, id=case)
    return clinical_analysis


def extract_proband_sex(proband):
    '''
    Patients are not routinely karyotyped, so karyotype information is not in
    OpenCGA. DECIPHER requires karyoptic sex, so the assumption is made that 
    if male, sex = 46XY and if female, sex = 46XX
        inputs:
            proband (dict): the proband information from the OpenCGA analysis
            client
        outputs:
            sex (str): the proband's assumed sex, or None if sex cannot be
            inferred
    '''
    if proband['sex']['id'] == "MALE":
        sex = "46_xy"
    elif proband['sex']['id'] == "FEMALE":
        sex = "46_xx"
    else:
        sex = None
    return sex


def extract_proband_phenotypes(proband):
    '''
    Extract the phenotypes from the case
        inputs:
            proband (dict): the proband information from the OpenCGA analysis
            client
        outputs:
            phenotype_list (list): a list of the proband's phenotypes in HPO
            terms or if there are none in opencga, an empty list
    '''
    phenotype_list = []
    if proband['phenotypes']:
        for phenotype in proband['phenotypes']:
            phenotype_list.append(phenotype['id'])
    return phenotype_list


def extract_proband_variants(interpretation):
    '''
    Extract the variants from the primary interpretaion of the case
       inputs:
            interpretation (dict): the interpretaion information from the
            OpenCGA analysis client; this has the primary findings of causative
            variants.
        outputs:
            variant_list (list): a list of interpreted variants
    '''
    variant_list = []
    for variant in interpretation:
        variant_type = variant['type']

        if variant_type in ("INDEL", "DELETION", "INSERTION"):
            # For INDELS, ref is stored as a dash in ['id'] need to get the
            # nomenclature from ['call']
            variant_id = variant['studies'][0]['files'][0]['call']['variantId']
        elif variant_type == "SNV":
            # For SNVS, ref is stored under the ['id'] key
            variant_id = variant['id']
        else:
            print("Could not determine variant type")

        zygosity = variant['studies'][0]['samples'][0]['data'][0]

        # Structure the variant information into a dictionary and add to a list
        # of variants that have been reviewed for this case
        data_dict = {
            'variant_id': variant_id,
            'type': variant_type,
            'zygosity': zygosity
            }
        variant_list.append(data_dict)
    return variant_list


def format_required_data_into_case_json(proband, sex, phenotypes, variants):
    '''
    Formats the data from opencga into a dictionary to be passed to a script
    that will be submitted to DECIPHER
        inputs:
            proband (dict): the proband information from the OpenCGA analysis
            client
            sex (str): the proband sex
            phenotypes (list): a list of phenotype data
            variants (list): a list of variant data
        outputs:
            case_dict (dict): a dictionary of case information that is needed
            to submit the case to DECIPHER
    '''
    # Format the data needed to submit a case to DECIPHER into a dictionary
    case_dict = {
        'sex': sex,
        'clinical_reference': proband['id'],
        'phenotype_list': phenotypes,
        'variant_list': variants
    }
    return case_dict


def main():
    '''
    The entry point function of this script. Parses the command line arguments
    and establishes an instance of the OpenCGA client. Calls other functions in
    the script to extract the required data for submission to DECIPHER
    '''
    parser = argparse.ArgumentParser(
                                description="",
                                formatter_class=(
                                   argparse.ArgumentDefaultsHelpFormatter
                                   )
                            )

    parser.add_argument("-k", "--configuration", help="OpenCGA login")
    parser.add_argument("-c", "--case",
                        help="OpenCGA case ID that is to be uploaded to DECIPHER"
                        )
    parser.add_argument("-s", "--study",
                        help="OpenCGA study where this case is located"
                        )

    args = parser.parse_args()

    # Extract and open JSON file containing OpenCGA login data
    login_details = args.configuration
    with open(login_details, 'r', encoding='utf-8') as f:
        datastore = json.load(f)

    # Retrieve keys from JSON
    USER = datastore["USER"]
    PASSWORD = datastore["PASSWORD"]

    # Create an instance of OpencgaClient passing the configuration
    config = ClientConfiguration(
        {"rest": {"host": "https://uat.eglh.app.zettagenomics.com/opencga/"}}
    )
    oc = OpencgaClient(config)
    oc.login(user=USER, password=PASSWORD)

    case_from_opencga = extract_case_from_opencga(args.case, args.study, oc)
    proband = case_from_opencga.get_result(result_pos=0)['proband']
    interpretation = case_from_opencga.get_result(result_pos=0)['interpretation']['primaryFindings']

    # Call functions to extract required data
    sex = extract_proband_sex(proband)
    phenotype_list = extract_proband_phenotypes(proband)
    variant_list = extract_proband_variants(interpretation)

    # Format the required data into a case dictionary
    info_to_send_to_decipher = format_required_data_into_case_json(
        proband, sex, phenotype_list, variant_list
        )

    with open(
        'case_phenotype_and_variant_data.json', 'w', encoding='utf-8'
    ) as f:
        json.dump(info_to_send_to_decipher, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
