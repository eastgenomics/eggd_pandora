import pandas as pd
import json
import argparse

def extract_clinvar_information(variant):
    '''
    Extract information from variant CSV and reformat into dictionary.
    Inputs:
        variant: row from variant dataframe with data for one variant
    outputs:
        clinvar_dict: dictionary of data to submit to clinvar 
    '''
    clinical_significance = check_clinical_significance(
        variant["Germline classification"]
        )
    comment = check_comment(variant["Comment on classification"])
    assembly = check_assembly(variant["Ref genome"])

    clinvar_dict = {
        'assertionCriteria': {
            'url': 'https://submit.ncbi.nlm.nih.gov/api/2.0/files/kf4l0sn8/uk-'\
                'practice-guidelines-for-variant-classification-v4-01-2020.pd'\
                'f/?format=attachment'
            },
        'clinvarSubmission': [{
            'clinicalSignificance': {
                'clinicalSignificanceDescription': clinical_significance,
                'comment': comment,
                'dateLastEvaluated': variant["Date last evaluated"]
            },
            'conditionSet': {
                'condition': [{'name': variant['Preferred condition name']}]
            },
            'localID': variant["Local ID"],
            'localKey': variant["Linking ID"],
            'observedIn': [{
                'affectedStatus': variant['Affected status'],
                'alleleOrigin': variant["Allele origin"],
                'collectionMethod': variant['Collection method']
            }],
            'recordStatus': "novel",
            'variantSet': {
                'variant': [{
                    'chromosomeCoordinates': {
                        'assembly': assembly,
                        'alternateAllele': variant['Alternate allele'],
                        'referenceAllele': variant['Reference allele'],
                        'chromosome': str(variant['Chromosome']),
                        'start': variant['Start']
                    },
                    'gene': [{
                        'symbol': variant["Gene symbol"]
                    }],
                }],
            },
        }],
    }

    clinvar_dict = if_nuh(variant["Organisation ID"], clinvar_dict)

    return clinvar_dict

def check_clinical_significance(clinical_significance_description):
    '''
    Tests that the value for clinical significance is valid according to what
    is accepted by ClinVar's API
    Inputs:
        clinical_significance_description: 'Germline classification' from 
        variant CSV
    Outputs:
        clinical_significance_description: 'Germline classification' from 
        variant CSV, validated to check it is compatible with ClinVar 
    '''

    clinical_significance_valid = [
        "Pathogenic",
        "Likely pathogenic",
        "Uncertain significance",
        "Likely benign",
        "Benign",
        "Pathogenic, low penetrance",
        "Uncertain risk allele",
        "Likely pathogenic, low penetrance",
        "Established risk allele",
        "Likely risk allele",
        "affects",
        "association",
        "drug response",
        "confers sensitivity",
        "protective",
        "other",
        "not provided"
    ]

    if clinical_significance_description in clinical_significance_valid:
        clinical_significance_description = clinical_significance_description

    elif str(clinical_significance_description) == "nan":
        raise RuntimeError(
            "No value provided for clinical significance 'Germline "
            "classification'. In order to submit to ClinVar this value must be"
            " complete"
        )

    else:
        raise RuntimeError(
            f"Clinical significance value {clinical_significance_description} "
            "is not in the list of strings for clinical significance that will"
            " be accepted by ClinVar \n"
            f"The list: {clinical_significance_valid}"
        )

    return clinical_significance_description

def check_comment(comment):
    '''
    Convert empty comments to "None" string that is a valid input to ClinVar.
    Inputs:
        comment (str): a comment
    Outputs:
        comment (str): a comment, edited to be "None" if empty in original df
    '''
    if str(comment) == "nan":
        comment = "None"
    return comment

def check_assembly(ref_genome):
    '''
    Work out assembly from the reference genome used to by VEP to process the
    data
    In our dias pipeline, this is the RefSeq cache in VEP 105

    For GRCh37, this will be GRCh37.p13
    For GRCh38, this will be GRCh38.p13

    Inputs:
        ref_genome (str): name of the reference genome for VEP for annotation
    Outputs:
        assembly (str): genome build of the reference genome (GRCh37 or GRCh38)
    '''
    if ref_genome == "GRCh37.p13":
        assembly = "GRCh37"
        print(
            f"Selected GRCh37 as assembly, because ref genome is {ref_genome}"
        )
    elif ref_genome == "GRCh38.p13":
        assembly = "GRCh38"
        print(
            f"Selected GRCh38 as assembly, because ref genome is {ref_genome}"
        )
    else:
        raise RuntimeError(
            f"Could not determine genome build from ref genome {ref_genome}"
        )
    return assembly

def if_nuh(organisation_id, clinvar_dict):
    '''
    Format submission correctly if this is an NUH case
    Inputs:
        organisation_id (int): ClinVar organisation ID for submitting lab (CUH
        or NUH)
        clinvar_dict (dict): dictionary of info to submit to clinvar
    Ouputs:
        clinvar_dict (dict): dictionary of info to submit to clinvar
    '''
    # If NUH
    if organisation_id == 509428:
        clinvar_dict['behalfOfID'] = organisation_id
    # If CUH, no changes need to be made
    elif organisation_id == 288359:
        pass
    else:
        raise ValueError(
            f"Value given for organisation ID {organisation_id} is not a valid"
            " option.\nValid options:\n288359 - CUH\n509428 - NUH"
        )
    return clinvar_dict

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

    parser.add_argument('--variant_csv')
    args = parser.parse_args()

    with open(args.variant_csv, 'r', encoding='utf-8') as f:
        df = pd.read_csv(f)

    for index, row in df.iterrows():
        clinvar_dict = extract_clinvar_information(row)

        file_name = args.variant_csv.split('/')[-1].split('.')[0]
        print(file_name)
        prefix = file_name + '-' + row['Local ID']

        with open(f"{prefix}_clinvar_data.json", 'w', encoding='utf-8') as f:
            json.dump(clinvar_dict, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
