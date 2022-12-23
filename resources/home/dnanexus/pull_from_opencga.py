# Import ClientConfiguration and OpencgaClient class
from pyopencga.opencga_config import ClientConfiguration
from pyopencga.opencga_client import OpencgaClient
import json
import argparse
import pandas as pd

parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("-k", "--configuration", help="OpenCGA login")

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

## Create main clients
users = oc.users
projects = oc.projects
studies = oc.studies
files = oc.files
jobs = oc.jobs
families = oc.families
individuals = oc.individuals
samples = oc.samples
cohorts = oc.cohorts
#panels = oc.panels
 
## Create analysis clients
#alignments = oc.alignment
variants = oc.variants
clinical = oc.clinical
ga4gh = oc.ga4gh
 
## Create administrative clients
admin = oc.admin
meta = oc.meta
variant_operations = oc.variant_operations

# sample_result = oc.samples.search(study='emee-glh@decipher_project:rare_disease_38', limit=5, include='id')
# sample_id_list = []
# for sample in sample_result.get_results():
#     print(sample)
#     sample_id_list.append(sample['id'])

# for sample_id in sample_id_list:
#     variant_response =  oc.variants.query(study='emee-glh@decipher_project:rare_disease_38', sample=sample_id, limit='3')
#     for variant in variant_response.get_results():
#         print('SAMPLE: ' + sample_id + ' CHROM: ' + variant['chromosome'] + ' POS: ' +  str(variant['start']) + ' REF: ' + variant['reference'] + ' ALT: ' + variant['alternate'])
#     indication_resp = oc.clinical.search_interpretation(study='emee-glh@decipher_project:rare_disease_38', limit='3')
#     for indication in indication_resp.get_results():
#         print(indication)


study='emee-glh@decipher_project:rare_disease_38'

def extract_case_information():
    case_list = []
    for individual in oc.individuals.search(study=study).result_iterator():
        phenotype_list = []
        if individual['disorders']:
            print(individual['disorders'])
            if individual['sex']['id'] == "MALE":
                proband_sex = "46_xy"
            if individual['sex']['id'] == "FEMALE":
                proband_sex = "46_xx"

            if individual['phenotypes']:
                for phenotype in individual['phenotypes']:
                    phenotype_list.append(phenotype['id'])
        
            case_dict = {
                'sex': proband_sex,
                'clinical_reference': individual['name'],
                'phenotype_list': phenotype_list
            }

            case_list.append(case_dict)

    with open('cases.json', 'w', encoding='utf-8') as f:
        json.dump(case_list, f, ensure_ascii=False, indent=4)


def extract_interpreted_variants(case_list):
    '''
    For a given case, extract the variants in open CGA under the most recent
    interpretation.
    '''
    variant_dict = {}
    
    for case in case_list:
        ## Query using the clinical info web service
        interpretation_info = oc.clinical.info(clinical_analysis=case, study=study)
        interpretation_info.print_results(fields='id,interpretation.id,type,proband.id')

        ## Select interpretation object 
        interpretation_object = interpretation_info.get_results()[0]['interpretation']

        ## Select interpretation id 
        interpretation_id = interpretation_info.get_results()[0]['interpretation']['id']

        proband_id = interpretation_info.get_results()[0]['proband']['name']

        ## Perform the query
        variants_reported = oc.clinical.info_interpretation(interpretations=interpretation_id, study=study)

        ## Define empty list to store the variants, genes and the tiering
        variant_list = []
        for variant in variants_reported.get_results()[0]['primaryFindings']:
            variant_type = variant['type']
            print(variant_type)
        
            if variant_type == "INDEL":
                variant_id = variant['studies'][0]['files'][0]['call']['variantId']
            elif variant_type == "SNV":
                variant_id = variant['id']
            else:
                print("Could not determine variant type")
          
            heterozygosity = variant['studies'][0]['samples'][0]['data'][0]

            data_dict = {'variant_id':variant_id,
                        'type': variant_type,
                        'heterozygosity': heterozygosity}
            variant_list.append(data_dict)

        variant_dict[proband_id] = variant_list
        #cases_and_variants_list.append(variant_dict)
    #print(variant_dict)
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(variant_dict, f, ensure_ascii=False, indent=4)

## Define an empty list to keep the case ids:
case_ids = []

## Iterate over the cases and retrieve the ids:
for case in oc.clinical.search(study=study, include='id').result_iterator():
    case_ids.append(case['id'])

print('There are {} cases in study {}'.format(len(case_ids), study))

selected_case="SAP-56130-1"

extract_case_information()
extract_interpreted_variants(case_ids)

# family_response = oc.families.search(study='emee-glh@decipher_project:rare_disease_38', families='SAP-56130-1', limit=5)
# print(family_response.get_results())

#result = oc.individuals.search(study='emee-glh rd_grch38', limit=5, include='id')
# result = oc.ga4gh.search_variants()
# print(result.responses)

# # Show as dataframe
# df = pd.DataFrame.from_dict(result.responses[0]['results'])
# print(df)

# # Show as JSON
# result_json = json.dumps(result.responses[0]['results'])
# print(result_json)
# for sample in result.responses[0]['results']:
#     sample_json = json.dumps(sample, indent=4)
#     print(sample_json)

# ariant_response =  oc.variants.query(study='emee-glh@rd_grch38:panel', sample="X218112-GM2012176-TWE-N-EGG4_S3_L001:0/1,1/1,1/2", limit='3')

