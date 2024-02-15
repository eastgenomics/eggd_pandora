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
    assembly = check_assembly(variant["Ref_genome"])

    clinvar_dict = {
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
    Work out assembly from the reference genome used to process the data
    In our dias pipeline this is the reference genome passed to eggd_conductor
    as "stage-sentieon_dnaseq.genome_fastagz" in the config file.

    For GRCh37, this will be hs37d5.fa
    For GRCh38, this will be GRCh38_GIABv3_no_alt_analysis_set_maskedGRC_decoys
    _MAP2K3_KMT2C_KCNJ18_noChr.fasta.gz

    Inputs:
        ref_genome (str): name of the reference genome used to make the VCF
    Outputs:
        assembly (str): genome build of the reference genome (GRCh37 or GRCh38)
    '''
    if ref_genome.split('.')[0] == "hs37d5":
        assembly = "GRCh37"
        print(
            f"Selected GRCh37 as assembly, because ref genome is {ref_genome}"
        )
    elif ref_genome.split('.')[0] == (
        "GRCh38_GIABv3_no_alt_analysis_set_maskedGRC_decoys_MAP2K3_KMT2C_KCN" \
        "J18_noChr"
    ):
        assembly = "GRCh38"
        print(
            f"Selected GRCh38 as assembly, because ref genome is {ref_genome}"
        )
    else:
        raise RuntimeError(
            f"Could not determine genome build from ref genome {ref_genome}"
        )
    return assembly

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

    with open(args.variant_csv, 'r') as f:
        df = pd.read_csv(f)

    for index, row in df.iterrows():
        clinvar_dict = extract_clinvar_information(row)
        if 'Instrument ID' and 'Specimen ID' in row:
            prefix = (
                str(row["Instrument ID"]) + '-' + row["Specimen ID"]
                + '-' + row['Local ID']
            )
        else:
            file_name = args.variant_csv.split('/')[-1].split('.')[0]
            print(file_name)
            prefix = file_name + '-' + row['Local ID']

        with open(f"{prefix}_clinvar_data.json", 'w', encoding='utf-8') as f:
            json.dump(clinvar_dict, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
