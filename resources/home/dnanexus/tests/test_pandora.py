#!/usr/bin/env python3
import pytest
from push_to_decipher import calculate_zygosity, calculate_variant_type, format_variant_json_for_decipher
from pull_from_opencga import extract_proband_sex, extract_proband_phenotypes, extract_proband_variants, format_required_data_into_case_json


class TestDecipher():
    '''
    Tests for checking function to push data to DECIPHER works
    '''
    # Define empty case dictionary and add sample variant_list. This is the
    # format that the submit_data_to_decipher() function in push_to_decipher.py
    # receives variant information. These test cases are used to test that the
    # submit_data_to_decipher() function submits the correct information
    case = {}
    case['variant_list'] = [
        {
            'variant_id': "12:21912765:G:GA,GAA",
            'type': 'INDEL',
            'zygosity': "1/2"
        },
        {
            "variant_id": "1:931131:C:CCCCT",
            "type": "DELETION",
            "zygosity": "0/1"
        },
        {
            "variant_id": "1:927003:C:T",
            "type": "SNV",
            "zygosity": "1|1"
        },
        {
            'variant_id': "12:21912765:G:GT,GTT,GTTT",
            'type': 'INDEL',
            'zygosity': "1/3"
        },
        {
            "variant_id": "1:14907:A:G",
            "type": "SNV",
            "zygosity": "0/0"
        }
    ]

    def test_zygosity(self):
        '''
        Test that the function calculate_zygosity() works out the zygosity from
        the input JSON case_phenotype_and_variant_data.json
        '''
        # The zygosity data will be under the key case['variant_list']
        zygosities = []
        for variant in self.case['variant_list']:
            zygosity = calculate_zygosity(variant, "46_xx")
            zygosities.append(zygosity)

        assert zygosities == [
            "heterozygous",
            "heterozygous",
            "homozygous",
            "heterozygous",
            "homozygous"
        ]

    @staticmethod
    def test_hemizygous_variants():
        '''
        Test that calculate_zygosity function works for hemizygous variants
        '''
        # Create test variant on Y that should be hemizygous
        test_variant = {
            "variant_id": "Y:2790748:T:TA",
            "type": "SNV",
            "zygosity": "0/1"
        }
        sex = '46_xy'
        test_zygosity = calculate_zygosity(test_variant, sex)
        assert test_zygosity == "hemizygous"

    def test_variant_type_calculated_correctly(self):
        '''
        Test that the  function calculate_variant_type works out the correct
        DECIPHER variant type for the input variant examples
        '''
        variant_types = []
        for variant in self.case['variant_list']:
            variant_type = calculate_variant_type(variant)
            variant_types.append(variant_type)
        # All the input variants are indels or snvs so they should all be 
        # classed as "sequence_variant". set() the list and assert that it only
        # contains one string of "sequence_variant"
        assert set(variant_types) == {"sequence_variant"}

    @staticmethod
    def test_invalid_variant_type():
        '''
        Test that the function calculate_variant_type() returns None if the 
        input variant type is incompatible with DECIPHER e.g. a CNV
        '''
        invalid_variant = {}
        invalid_variant['type'] = "CNV"
        variant_type = calculate_variant_type(invalid_variant)
        print(variant_type) 
        assert variant_type == None

    def test_zeros_and_duplicates_removed(self):
        '''
        Test that for each variant in the variant list the correct ref and alt
        information is extracted and submitted
        This test ensures variants that are not present i.e. that have a 0
        value for their zygosity are not submitted and that homozygous
        variants are not submitted twice
        '''
        variant_list = []
        for variant in self.case['variant_list']:
            variant_dict_list = format_variant_json_for_decipher(variant, 123, "heterozygous", "structural_variant")
            if variant_dict_list is not None:

                for variant_dict in variant_dict_list:
                    variant_list.append(variant_dict)
        print(variant_list)
        # Assert that the variants have been worked out correctly and that the
        # homozygous variants have not been added to the list twice
        assert variant_list == [
        {'data': {'type': 'Variant',
        'attributes': {
            'person_id': 123,
            'variant_class': 'structural_variant',
            'assembly': 'GRCh38',
            'chr': '12',
            'start': '21912765',
            'ref_sequence': 'G',
            'alt_sequence': 'GA',
            'inheritance': 'unknown',
            'genotype': 'heterozygous',
            'can_be_public': False
            }
        }
        },
        {'data': {'type': 'Variant',
        'attributes': {
            'person_id': 123,
            'variant_class': 'structural_variant',
            'assembly': 'GRCh38',
            'chr': '12',
            'start': '21912765',
            'ref_sequence': 'G',
            'alt_sequence': 'GAA',
            'inheritance': 'unknown',
            'genotype': 'heterozygous',
            'can_be_public': False
            }
        }
        },
        {'data': {'type': 'Variant',
        'attributes': {
            'person_id': 123,
            'variant_class':
            'structural_variant',
            'assembly': 'GRCh38',
            'chr': '1',
            'start': '931131',
            'ref_sequence': 'C',
            'alt_sequence': 'CCCCT',
            'inheritance': 'unknown',
            'genotype': 'heterozygous',
            'can_be_public': False
                }
            }
        },
        {'data': {'type': 'Variant',
        'attributes': {
            'person_id': 123,
            'variant_class': 'structural_variant',
            'assembly': 'GRCh38',
            'chr': '1',
            'start': '927003',
            'ref_sequence': 'C',
            'alt_sequence': 'T',
            'inheritance': 'unknown',
            'genotype': 'heterozygous',
            'can_be_public': False
                }
            }
        },
        {'data': {'type': 'Variant',
        'attributes': {
            'person_id': 123,
            'variant_class': 'structural_variant',
            'assembly': 'GRCh38',
            'chr': '12',
            'start': '21912765',
            'ref_sequence': 'G',
            'alt_sequence': 'GT',
            'inheritance': 'unknown',
            'genotype': 'heterozygous',
            'can_be_public': False
                }
            }
        },
        {'data': {'type': 'Variant',
        'attributes': {
            'person_id': 123,
            'variant_class': 'structural_variant',
            'assembly': 'GRCh38',
            'chr': '12',
            'start': '21912765',
            'ref_sequence': 'G',
            'alt_sequence': 'GTTT',
            'inheritance': 'unknown',
            'genotype': 'heterozygous',
            'can_be_public': False
            }
            }
        },
    ]


class TestOpenCGA():
    '''
    Tests for checking function to pull data from OpenCGA
    '''
    proband = {"id": "12345", "sex": {"id": "MALE"},
                "phenotypes": [
                    {
                        "id": "HP:0000119"
                    },
                    {
                        "id": "HP:0000121"
                    },
                    {
                        "id": "HP:0000377"
                    }
                ]
            }
    interpretation = [
        {'type': "INDEL", "studies": [
            {"samples": [{"data": ["0/1"]}],
             "files": [{"call": {"variantId": "1:10108:C:CT"}}]
            }]
        },
        {'type': "SNV", 'id': "1:927003:C:T", "studies": [
            {"samples":[{'data': ['1|1']}]},
        ]
        }
    ]

    def test_proband_sex_extraction(self):
        '''
        Test that function to determine proband sex works
        '''
        proband_sex = extract_proband_sex(self.proband)
        assert proband_sex == "46_xy"

    def test_proband_phenotype_extraction(self):
        '''
        Test that the function to extract proband phenotypes works
        '''
        phenotype_list = extract_proband_phenotypes(self.proband)
        assert phenotype_list == ["HP:0000119", "HP:0000121", "HP:0000377"]

    def test_proband_variant_extraction(self):
        '''
        Test that the function to extract proband variants works
        '''
        variant_list = extract_proband_variants(self.interpretation)
        assert variant_list == [
            {'variant_id': "1:10108:C:CT",
            'type': 'INDEL',
            'zygosity': '0/1'},
            {'variant_id': "1:927003:C:T",
            'type': 'SNV',
            'zygosity': '1|1'}
        ]

    def test_case_json_formatted_correctly(self):
        '''
        Test that the case dictionary is formatted correctly
        '''
        case_dictionary = format_required_data_into_case_json(
            self.proband,
            "46_xy",
            ["HP:0000119", "HP:0000121", "HP:0000377"],
            [{'variant_id': "1:10108:C:CT",
            'type': 'INDEL',
            'zygosity': '0/1'}]
            )
        assert case_dictionary == {
        'sex': "46_xy",
        'clinical_reference': "12345",
        'phenotype_list': ["HP:0000119", "HP:0000121", "HP:0000377"],
        'variant_list': [{
            'variant_id': "1:10108:C:CT",
            "type": 'INDEL',
            'zygosity': '0/1'}]
        }


if __name__ == "__main__":
    opencga = TestOpenCGA()
    decipher = TestDecipher()
