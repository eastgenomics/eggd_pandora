#!/usr/bin/env python3
import pandas as pd
import pytest
import os
from push_to_decipher import *
from pull_from_opencga import *
from pull_from_csv import *
from push_to_clinvar import *


class TestDecipher:
    """
    Tests for checking function to push data to DECIPHER works
    """

    # Define empty case dictionary and add sample variant_list. This is the
    # format that the submit_data_to_decipher() function in push_to_decipher.py
    # receives variant information. These test cases are used to test that the
    # submit_data_to_decipher() function submits the correct information
    case = {}
    case["variant_list"] = [
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
        """
        Test that the function calculate_zygosity() works out the zygosity from
        the input JSON case_phenotype_and_variant_data.json
        """
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
            "homozygous",
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
        """
        Test that the  function calculate_variant_type works out the correct
        DECIPHER variant type for the input variant examples
        """
        variant_types = []
        for variant in self.case["variant_list"]:
            variant_type = calculate_variant_type(variant)
            variant_types.append(variant_type)
        # All the input variants are indels or snvs so they should all be
        # classed as "sequence_variant". set() the list and assert that it only
        # contains one string of "sequence_variant"
        assert set(variant_types) == {"sequence_variant"}

    @staticmethod
    def test_invalid_variant_type():
        """
        Test that the function calculate_variant_type() returns None if the
        input variant type is incompatible with DECIPHER e.g. a CNV
        """
        invalid_variant = {}
        invalid_variant["type"] = "CNV"
        variant_type = calculate_variant_type(invalid_variant)
        print(variant_type)
        assert variant_type == None

    def test_zeros_and_duplicates_removed(self):
        """
        Test that for each variant in the variant list the correct ref and alt
        information is extracted and submitted
        This test ensures variants that are not present i.e. that have a 0
        value for their zygosity are not submitted and that homozygous
        variants are not submitted twice
        """
        variant_list = []
        for variant in self.case["variant_list"]:
            variant_dict_list = format_variant_json_for_decipher(
                variant, 123, "heterozygous", "structural_variant"
            )
            if variant_dict_list is not None:
                for variant_dict in variant_dict_list:
                    variant_list.append(variant_dict)

        # Assert that the variants have been worked out correctly and that the
        # homozygous variants have not been added to the list twice

        assert len(variant_list) == 6

        for variant in variant_list:
            assert variant in [
                {
                    "data": {
                        "type": "Variant",
                        "attributes": {
                            "person_id": 123,
                            "variant_class": "structural_variant",
                            "assembly": "GRCh38",
                            "chr": "12",
                            "start": "21912765",
                            "ref_sequence": "G",
                            "alt_sequence": "GAA",
                            "inheritance": "unknown",
                            "genotype": "heterozygous",
                            "can_be_public": False,
                        },
                    }
                },
                {
                    "data": {
                        "type": "Variant",
                        "attributes": {
                            "person_id": 123,
                            "variant_class": "structural_variant",
                            "assembly": "GRCh38",
                            "chr": "12",
                            "start": "21912765",
                            "ref_sequence": "G",
                            "alt_sequence": "GA",
                            "inheritance": "unknown",
                            "genotype": "heterozygous",
                            "can_be_public": False,
                        },
                    }
                },
                {
                    "data": {
                        "type": "Variant",
                        "attributes": {
                            "person_id": 123,
                            "variant_class": "structural_variant",
                            "assembly": "GRCh38",
                            "chr": "1",
                            "start": "931131",
                            "ref_sequence": "C",
                            "alt_sequence": "CCCCT",
                            "inheritance": "unknown",
                            "genotype": "heterozygous",
                            "can_be_public": False,
                        },
                    }
                },
                {
                    "data": {
                        "type": "Variant",
                        "attributes": {
                            "person_id": 123,
                            "variant_class": "structural_variant",
                            "assembly": "GRCh38",
                            "chr": "1",
                            "start": "927003",
                            "ref_sequence": "C",
                            "alt_sequence": "T",
                            "inheritance": "unknown",
                            "genotype": "heterozygous",
                            "can_be_public": False,
                        },
                    }
                },
                {
                    "data": {
                        "type": "Variant",
                        "attributes": {
                            "person_id": 123,
                            "variant_class": "structural_variant",
                            "assembly": "GRCh38",
                            "chr": "12",
                            "start": "21912765",
                            "ref_sequence": "G",
                            "alt_sequence": "GTTT",
                            "inheritance": "unknown",
                            "genotype": "heterozygous",
                            "can_be_public": False,
                        },
                    }
                },
                {
                    "data": {
                        "type": "Variant",
                        "attributes": {
                            "person_id": 123,
                            "variant_class": "structural_variant",
                            "assembly": "GRCh38",
                            "chr": "12",
                            "start": "21912765",
                            "ref_sequence": "G",
                            "alt_sequence": "GT",
                            "inheritance": "unknown",
                            "genotype": "heterozygous",
                            "can_be_public": False,
                        },
                    }
                },
            ]


class TestOpenCGA:
    """
    Tests for checking function to pull data from OpenCGA
    """

    proband = {
        "id": "12345",
        "sex": {"id": "MALE"},
        "phenotypes": [
            {"id": "HP:0000119"},
            {"id": "HP:0000121"},
            {"id": "HP:0000377"},
        ],
    }
    interpretation = [
        {
            "type": "INDEL",
            "studies": [
                {
                    "samples": [{"data": ["0/1"]}],
                    "files": [{"call": {"variantId": "1:10108:C:CT"}}],
                }
            ],
        },
        {
            "type": "SNV",
            "id": "1:927003:C:T",
            "studies": [
                {"samples": [{"data": ["1|1"]}]},
            ],
        },
    ]

    def test_proband_sex_extraction(self):
        """
        Test that function to determine proband sex works
        """
        proband_sex = extract_proband_sex(self.proband)
        assert proband_sex == "46_xy"

    def test_proband_phenotype_extraction(self):
        """
        Test that the function to extract proband phenotypes works
        """
        phenotype_list = extract_proband_phenotypes(self.proband)
        assert phenotype_list == ["HP:0000119", "HP:0000121", "HP:0000377"]

    def test_proband_variant_extraction(self):
        """
        Test that the function to extract proband variants works
        """
        variant_list = extract_proband_variants(self.interpretation)
        assert variant_list == [
            {"variant_id": "1:10108:C:CT", "type": "INDEL", "zygosity": "0/1"},
            {"variant_id": "1:927003:C:T", "type": "SNV", "zygosity": "1|1"},
        ]

    def test_case_json_formatted_correctly(self):
        """
        Test that the case dictionary is formatted correctly
        """
        case_dictionary = format_required_data_into_case_json(
            self.proband,
            "46_xy",
            ["HP:0000119", "HP:0000121", "HP:0000377"],
            [{"variant_id": "1:10108:C:CT",
              "type": "INDEL",
              "zygosity": "0/1"}],
        )
        assert case_dictionary == {
            "sex": "46_xy",
            "clinical_reference": "12345",
            "phenotype_list": ["HP:0000119", "HP:0000121", "HP:0000377"],
            "variant_list": [
                {"variant_id": "1:10108:C:CT",
                 "type": "INDEL",
                 "zygosity": "0/1"}
            ],
        }


class TestCSV:
    """
    Tests for pull_from_csv.py script
    """

    errors = []
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "test_data/test_variant.csv")

    with open(filename, "r") as f:
        test_data = pd.read_csv(f)

    def test_clinical_significance_invalid(self):
        """
        Check a Runtime Error is raised if the string passed for clinical
        significance is not a valid string for ClinVar.
        """
        with pytest.raises(RuntimeError):
            check_clinical_significance("Invalid")

    def test_clinical_significance_empty(self):
        """
        Check a Runtime Error is raised if the string "nan" is passed for
        clinical significance. This is the value that would be present if the
        dataframe empty for clinical significance was empty.
        """
        with pytest.raises(RuntimeError):
            check_clinical_significance("nan")

    def test_extract_clinvar_information(self):
        """
        Test that clinvar information is extracted from df as expected
        """

        variant = self.test_data.iloc[0]
        clinvar_json = extract_clinvar_information(variant)

        assert clinvar_json == (
            {
                "assertionCriteria": {
                    "url": "https://submit.ncbi.nlm.nih.gov/api/2.0/files/kf4l"
                    "0sn8/uk-practice-guidelines-for-variant-classification-v4"
                    "-01-2020.pdf/?format=attachment"
                },
                "clinvarSubmission": [
                    {
                        "clinicalSignificance": {
                            "clinicalSignificanceDescription": "Pathogenic",
                            "comment": "Test comment",
                            "dateLastEvaluated": "2022-10-18",
                        },
                        "conditionSet": {"condition": [
                            {"name": "Cystic fibrosis"}
                        ]},
                        "localID": "uid_xxxx",
                        "localKey": "uid_yyyy",
                        "observedIn": [
                            {
                                "affectedStatus": "yes",
                                "alleleOrigin": "germline",
                                "collectionMethod": "clinical testing",
                            }
                        ],
                        "recordStatus": "novel",
                        "variantSet": {
                            "variant": [
                                {
                                    "chromosomeCoordinates": {
                                        "assembly": "GRCh37",
                                        "alternateAllele": "CA",
                                        "referenceAllele": "C",
                                        "chromosome": "7",
                                        "start": 117232266,
                                    },
                                    "gene": [{"symbol": "CFTR"}],
                                }
                            ]
                        },
                    }
                ],
            }
        )

    def test_assembly_38(self):
        """
        Check build 38 is selected if dias standard VEP build 38 reference
        genome is used
        """
        assert determine_assembly("GRCh38.p13") == "GRCh38"

    def test_assembly_37(self):
        """
        Check build 37 is selected if dias standard VEP build 37 reference
        genome is used
        """
        assert determine_assembly("GRCh37.p13") == "GRCh37"

    def test_assembly_invalid(self):
        """
        Check error is raised if unfamiliar reference genome is provided to
        check_assembly function
        """
        with pytest.raises(RuntimeError):
            determine_assembly("incorrect_reference_genome.fa.gz")

    def test_nuh_org_url_added(self):
        """
        Test that behalfOrgID field is added if organisation is NUH
        """
        assert add_lab_specific_guidelines(509428, {}) == {
            "assertionCriteria":{
                'url': 'https://submit.ncbi.nlm.nih.gov/api/2.0/files/iptxgqju'
                '/uk-practice-guidelines-for-variant-classification-v4-01-2020'
                '.pdf/?format=attachment'}
        }

    def test_no_change_if_cuh(self):
        """
        Test that clinvar_dict is not changed if organisation is CUH
        """
        assert add_lab_specific_guidelines(288359, {}) == {
            "assertionCriteria":{
                'url': 'https://submit.ncbi.nlm.nih.gov/api/2.0/files/kf4l0sn8'
                '/uk-practice-guidelines-for-variant-classification-v4-01-2020'
                '.pdf/?format=attachment'}
        }

    def test_error_if_invalid_org_id(self):
        """
        Test that error is raised if organisation is invalid
        """
        with pytest.raises(ValueError) as error:
            add_lab_specific_guidelines(12345, {})


class TestClinvar:
    """
    Tests for push_to_clinvar.py script
    """

    api_key = "xxxxxxxx"

    def test_select_api_url(self):
        """
        Test error raised if value given to select_api_url is neither True nor
        False
        """
        with pytest.raises(RuntimeError):
            select_api_url("Undecided")

    def test_select_testing_api_url(self):
        """
        Test that API url for testing endpoint is selected if value given to
        select_api_url is True i.e. if clinvar_testing = True
        """
        assert (
            select_api_url(True) == "https://submit.ncbi.nlm.nih.gov/apite"
            "st/v1/submissions"
        )

    def test_make_headers_works(self):
        """
        Test that headers are constructed correctly
        """
        assert make_headers(self.api_key) == {
            "SP-API-KEY": "xxxxxxxx",
            "Content-type": "application/json",
        }

    def test_make_headers_with_non_string_input(self):
        """
        Check TypeError raised when non string input to make_headers
        """
        with pytest.raises(TypeError):
            make_headers(12345)

if __name__ == "__main__":
    opencga = TestOpenCGA()
    decipher = TestDecipher()
    csv = TestCSV()
    clinvar = TestClinvar()
