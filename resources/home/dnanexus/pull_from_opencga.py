# Import ClientConfiguration and OpencgaClient class
import json
import argparse
from pyopencga.opencga_config import ClientConfiguration
from pyopencga.opencga_client import OpencgaClient

parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("-k", "--configuration", help="OpenCGA login")
parser.add_argument("-c", "--case", help="OpenCGA case ID that is to be uploaded to DECIPHER")
parser.add_argument("-s", "--study", help="OpenCGA study where this case is located")

args = parser.parse_args()
print(args)

# Extract and open JSON file containing OpenCGA login data
login_details = args.configuration
with open(login_details, 'r') as f:
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

def extract_case_information(case, study):
    '''
    Give a case from a study in OpenCGA, return a json for the case proband with
    all the information needed to submit that case to DECIPHER
        inputs:
            case (str) = the case ID in OpenCGA
            study (str) = the study where this case is located in OpenCGA
        outputs:
            a json of all the information needed to submit a case to DECIPHER:
            proband id
            proband sex
            variants
            phentypes
    '''
    # Find this case from the Analysis - Clinical client of the OpenCGA API
    clinical_analysis = oc.clinical.search(study=study, id=case)

    # Retrieve the proband sex
    proband = clinical_analysis.get_result(result_pos=0)['proband']
    if proband['sex']['id'] == "MALE":
        sex = "46_xy"
    if proband['sex']['id'] == "FEMALE":
        sex = "46_xx"

    # Retrieve the phenotypes
    phenotype_list = []
    if proband['phenotypes']:
        for phenotype in proband['phenotypes']:
            phenotype_list.append(phenotype['id'])

    # Retrieve the variants. Only those that have the "REVIEWED" status.
    # Currently variants are only searched for proband

    # Get the interpretation info for the Primary Interpretation
    interpretation = clinical_analysis.get_result(result_pos=0)['interpretation']

    # Extract the variant information from the Primary Interpretation
    variant_list = []
    for variant in interpretation['primaryFindings']:
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

        heterozygosity = variant['studies'][0]['samples'][0]['data'][0]

        # Structure the variant information into a dictionary and add to a list
        # of variants that have been reviewed for this case
        data_dict = {'variant_id': variant_id,
                    'type': variant_type,
                    'heterozygosity': heterozygosity}
        variant_list.append(data_dict)

    # Format the information needed to submit a case to DECIPHER into a dictionary
    case_dict = {
        'sex': sex,
        'clinical_reference': proband['id'],
        'phenotype_list': phenotype_list,
        'variant_list': variant_list
    }

    return case_dict

if args.case and args.study:
    info_to_send_to_decipher = extract_case_information(args.case, args.study)
    with open('case_phenotype_and_variant_data.json', 'w', encoding='utf-8') as f:
        json.dump(info_to_send_to_decipher, f, ensure_ascii=False, indent=4)
