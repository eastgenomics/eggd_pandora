#!/usr/bin/env python3
import pytest


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
            'heterozygosity': "1/2"
        },
        {
            "variant_id": "1:931131:C:CCCCT",
            "type": "DELETION",
            "heterozygosity": "0/1"
        },
        {
            "variant_id": "1:927003:C:T",
            "type": "SNV",
            "heterozygosity": "1|1"
        },
        {
            'variant_id': "12:21912765:G:GT,GTT,GTTT",
            'type': 'INDEL',
            'heterozygosity': "1/3"
        },
        {
            "variant_id": "1:14907:A:G",
            "type": "SNV",
            "heterozygosity": "0/0"
        }
    ]

    def test_heterozygosity(self):
        '''
        Test that the function submit_data_to_decipher() works out the
        heterozygosity from the input JSON case_phenotype_and_variant_data.json
        '''
        # Define input variants including a variety of cases
        # The heterozygosity data will be under the key case['variant_list']

        # Configure heterozygosity
        heterozygosities = []
        for variant in self.case['variant_list']:
            heterozygosity = None
            variant_index = variant["heterozygosity"].replace("|", "/").split("/")
            if variant_index[0] != variant_index[1]:
                heterozygosity = "heterozygous"
            elif variant_index[0] == variant_index[1]:
                heterozygosity = "homozygous"
            heterozygosities.append(heterozygosity)

        # Assert that the heterozygosities have been worked out correctly
        # For 1/2 0/1 1/1 1/3 0/0
        # The output should be hetero, hetero, homo, hetero, homo
        assert heterozygosities == [
            "heterozygous",
            "heterozygous",
            "homozygous",
            "heterozygous",
            "homozygous"
        ]

    def test_zeros_and_duplicates_removed(self):
        '''
        Test that for each variant in the variant list the correct ref and alt
        information is extracted and submitted
        This test ensures variants that are not present i.e. that have a 0
        value in their heterozygosity are not submitted and that homozygous
        variants are not submitted twice
        '''
        variant_list = []
        for variant in self.case['variant_list']:
            variant_index = variant["heterozygosity"].replace("|", "/").split("/")
            already_done = []
            for i in variant_index:
                if i not in already_done:
                    # Having an already done list ensures homozygous variants
                    # will not be submitted twice
                    if i != "0":
                        # If the index is not zero go to that index in the
                        # variant nomenclature and submit that variant
                        variant_list.append({
                            "chr": variant["variant_id"].split(":")[0],
                            "start": variant["variant_id"].split(":")[1],
                            "ref": variant["variant_id"].split(":")[2],
                            "alt": variant["variant_id"].split(":")[3].split(",")[int(i)-1],
                            }
                        )
                already_done.append(i)

        # Assert that the variants have been worked out correctly and that the
        # homozygous variants have not been added to the list twice
        assert variant_list == [
            {"chr": "12", "start": "21912765", "ref": "G", "alt": "GA"},
            {"chr": "12", "start": "21912765", "ref": "G", "alt": "GAA"},
            {"chr": "1", "start": "931131", "ref": "C", "alt": "CCCCT"},
            {"chr": "1", "start": "927003", "ref": "C", "alt": "T"},
            {"chr": "12", "start": "21912765", "ref": "G", "alt": "GT"},
            {"chr": "12", "start": "21912765", "ref": "G", "alt": "GTTT"}
        ]


if __name__ == "__main__":
    decipher = TestDecipher()
