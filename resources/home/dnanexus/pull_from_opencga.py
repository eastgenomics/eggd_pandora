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

## Define an empty list to keep the case ids:
case_ids = []

## Iterate over the cases and retrieve the ids:
for case in oc.clinical.search(study=study, include='id').result_iterator():
    case_ids.append(case['id'])

print('There are {} cases in study {}'.format(len(case_ids), study))

## Select a random case from the list
import random
if case_ids != []:
    
    selected_case = random.choice(case_ids)
    print('Case selected for analysis is {}'.format(selected_case))
else:
    print('There are no cases in the study', study)

selected_case="SAP-56130-1"

def extract_interpreted_variants(case):
    '''
    For a given case, extract the variants in open CGA under the most recent
    interpretation.
    '''
    ## Query using the clinical info web service
    interpretation_info = oc.clinical.info(clinical_analysis=selected_case, study=study)
    interpretation_info.print_results(fields='id,interpretation.id,type,proband.id')

    ## Select interpretation object 
    interpretation_object = interpretation_info.get_results()[0]['interpretation']

    ## Select interpretation id 
    interpretation_id = interpretation_info.get_results()[0]['interpretation']['id']

    ## Uncomment next line to display an interactive JSON viewer
    # JSON(interpretation_object)

    print('The interpretation id for case {} is {}'.format(selected_case, interpretation_object['id'] ))



    ## Perform the query
    variants_reported = oc.clinical.info_interpretation(interpretations=interpretation_id, study=study)

    ## Define empty list to store the variants, genes and the tiering
    variant_list = []
    for variant in variants_reported.get_results()[0]['primaryFindings']:
        print(variant)
        variant_id = variant['id']

        gene_id = variant['evidences'][0]['genomicFeature']['id']

        gene_name = variant['evidences'][0]['genomicFeature']['geneName']

        variant_type = variant['type']

        heterozygosity = variant['studies'][0]['samples'][0]['data'][0]

        data_dict = {'variant_id':variant_id,
                    'gene_id':gene_id,
                    'gene_name':gene_name,
                    'type': variant_type,
                    'heterozygosity': heterozygosity}
        variant_list.append(data_dict)

    print(variant_list)
    variant_dict = {}
    variant_dict["variants"] = variant_list

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(variant_list, f, ensure_ascii=False, indent=4)


extract_interpreted_variants(selected_case)

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
