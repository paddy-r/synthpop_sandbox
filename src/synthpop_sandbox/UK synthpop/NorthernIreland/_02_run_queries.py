##### Meta #####
# Author: Hugh Rice
# Version: 1.0
# Date:  2025-09-16
# About: Download all data/resources from web as required


### Imports ###
import os
from os.path import dirname as up
import pandas as pd
import urllib.request as url
import requests
import json
from io import StringIO
from _user_functions import *


# Urban-rural classification (RUC)
RUC_URL = "https://www.nisra.gov.uk/sites/nisra.gov.uk/files/publications/geography-data-zone-and-super-data-zone-lookups.xlsx"
RUC_SHEET = "DZ21_Urban_mixed_rural_lookup"
RUC_RAW = os.path.join(PERSISTENT_DATA_PATH, 'ni_ruc_raw.csv')
RUC_VAR_MAP = {'DZ2021_code': 'areacode',
               'Urban_status': 'urban_status',
               }
RUC_URBAN = 'Urban'  # Binary identifier; other is "Urban_mixed_rural_status" and so not appropriate
RUC_OUT = os.path.join(OUTPUT_PATH, 'census2021_c1_urbanrural_master.csv')

# Population data - manually downloaded
POP_DICT = {'hh': {'file': os.path.join(PERSISTENT_DATA_PATH, "census-2021-ms-e01.xlsx"),
                   'sheet': "DZ",
                   'header_row': 5,
                   'var_map': {'Geography code': 'areacode',
                               'All households': 'number',
                               },
                   'outfile': os.path.join(OUTPUT_PATH, "census2021_pop_hh.csv"),
                   },
            'ind': {'file': os.path.join(PERSISTENT_DATA_PATH, "census-2021-ms-a01.xlsx"),
                    'sheet': 'DZ',
                    'header_row': 5,
                    'var_map': {'Geography Code': 'areacode',
                                'All usual residents': 'number',
                                },
                    'outfile': os.path.join(OUTPUT_PATH, "census2021_pop_ind.csv"),
                    },
            }

# All defaults for automated constraint data retrieval from NISRA
AREACODE_COL_DEFAULT = 'Census 2021 Data Zone Code'
AREACODE_DEFAULT = 'areacode'
COUNT_COL_DEFAULT = 'Count'
COUNT_DEFAULT = 'count'
HH_LEVEL_DEFAULT = True
HRP_DEFAULT = False
HRP_COL_DEFAULT = 'Household Reference Person Indicator Code'
HRP_HEADERS = ["Household Reference Person Indicator Code",
               "Household Reference Person Indicator Label",
               ]
NATION_SOURCE_DEFAULT = 'Scotland'  # Specify which nation group to grab microdata from - workaround w/o all-UK process
LABEL_JOINER = '%'
VARIABLE_JOINER = '_'  # Should be reserved string for separating multivariate constraints later, e.g. for validation

# Constraints data dictionary, fully automated
# 1. Constraint label should indicate specific variable type, e.g. age11 is the NISRA 11-category age spec
# 2. URL is found manually using the NISRA custom table builder here: https://build.nisra.gov.uk/en/custom/dataset
# 3. The URL is modified at runtime to retrieve the corresponding CSV - method via email from NISRA
# 4. var_map maps the variables as given in the NISRA dataset to those required for the final constraint format
# 5. These should be in the same order as appear in the final format, as should those in category_map
# 6. Each value in var_map has a corresponding key in category_map, which maps to the final constraint categories
# 7. hh_level and hrp specify whether data are at hh (or ind) level, or HRP level, as these require specific processing
CONSTRAINTS = {
    'sex2_age11_ind': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=PEOPLE&v=DZ21&v=AGE_BAND_AGG11&v=UR_SEX',
                       'var_map': {'Sex Code': 'sex',
                                   'Age - 11 Categories Code': 'age',
                                   },
                       'category_map': {'sex': {1: 'f',
                                                2: 'm',
                                                },
                                        'age': {1: '00_15',
                                                2: '16_24',
                                                3: '25_34',
                                                4: '25_34',
                                                5: '35_49',
                                                6: '35_49',
                                                7: '35_49',
                                                8: '50_64',
                                                9: '50_64',
                                                10: '50_64',
                                                11: '65_over',
                                                },
                                        },
                       'hh_level': False,
                       },
    'qual8_ind': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=PEOPLE&v=DZ21&v=HIGHEST_QUALIFICATION',
                  'var_map': {'Qualifications (Highest Level) Code': 'education',
                              },
                  'category_map': {'education': {0: 'no_qualification',
                                                 1: 'lower_school',
                                                 2: 'upper_further',
                                                 3: 'education_other',
                                                 4: 'upper_further',
                                                 5: 'degree_level',
                                                 6: 'education_other',
                                                 # -8: 'no_qualification',  # Remove to account for over-16s only
                                                 },
                                   },
                  'hh_level': False,
                  },
    'ethnicity13_ind': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=PEOPLE&v=DZ21&v=ETHNIC_GROUP_INTERMEDIATE',
                    'var_map': {'Ethnic Group Code': 'ethnicity',
                                },
                    'category_map': {'ethnicity': {1: 'white',
                                                   2: 'white',
                                                   3: 'white',
                                                   4: 'asian',
                                                   5: 'asian',
                                                   6: 'asian',
                                                   7: 'asian',
                                                   8: 'ethnicity_other',
                                                   9: 'asian',
                                                   10: 'african',
                                                   11: 'caribbean_black',
                                                   12: 'mixed',
                                                   13: 'ethnicity_other',
                                                   },
                                     },
                    'hh_level': False,
                    },
    'marital6_ind': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=PEOPLE&v=DZ21&v=MAR_CP_STATUS_AGG6',
                     'var_map': {'Marital and Civil Partnership Status - 6 Categories Code': 'partnership',
                                 },
                     'category_map': {'partnership': {1: 'single',
                                                      2: 'married_civil',
                                                      3: 'separated',
                                                      4: 'divorced',
                                                      5: 'widowed',
                                                      # -8: 'single',  # Remove to account for over-16s only
                                                      }
                                      },
                     'hh_level': False,
                     },
    'health5_ind': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=PEOPLE&v=DZ21&v=HEALTH_IN_GENERAL',
                    'var_map': {'Health in General Code': 'health',
                                },
                    'category_map': {'health': {1: 'very_good',
                                                2: 'good',
                                                3: 'fair',
                                                4: 'bad',
                                                5: 'bad',
                                                },
                                     },
                    'hh_level': False,
                    },
    'activity12_ind': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=PEOPLE&v=DZ21&v=ECONOMIC_ACTIVITY_AGG12',
                       'var_map': {'Economic Activity - 12 Categories Code': 'activity',
                                   },
                       'category_map': {'activity': {1: 'employed',
                                                     2: 'self_employed',
                                                     3: 'self_employed',
                                                     4: 'unemployed',
                                                     5: 'student',
                                                     6: 'student',
                                                     7: 'retired',
                                                     8: 'student',
                                                     9: 'looking_after_home',
                                                     10: 'lts_disabled',
                                                     11: 'activity_other',
                                                     # -8: 'activity_other',  # Remove to account for over-16s only
                                                     },
                                        },
                       'hh_level': False,
                       'nation_source': 'EnglandWales',
                       },
    'industry7_ind': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=PEOPLE&v=DZ21&v=INDUSTRY_AGG9',
                      'var_map': {'Industry (Current) - 9 Categories Code': 'industry',
                                  },
                      'category_map': {'industry': {1: 'abde_agriculture_energy_water',
                                                    2: 'c_manufacturing',
                                                    3: 'f_construction',
                                                    4: 'gi_distribution_hotels_restaurants',
                                                    5: 'hj_transport_communication',
                                                    6: 'klmn_financial_etc',
                                                    7: 'opq_public_admin_education_health',
                                                    8: 'rstu_other',
                                                    # -8: 'rstu_other',
                                                    },
                                       },
                      'hh_level': False,
                      },
    'centralheating2_hh': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=HOUSEHOLD&v=DZ21&v=HH_CENTRAL_HEATING_IND',
                           'var_map': {'Central Heating - 2 Categories Code': 'heating',
                                       },
                           'category_map': {'heating': {0: 'without_heating',
                                                        1: 'with_heating',
                                                        },
                                            },
                           },
    'deprivation5_hh': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=HOUSEHOLD&v=DZ21&v=HH_DEPRIVATION',
                        'var_map': {'Household Deprivation Code': 'deprivation',
                                    },
                        'category_map': {'deprivation': {1: 'deprivation_0',
                                                         2: 'deprivation_1',
                                                         3: 'deprivation_2',
                                                         4: 'deprivation_3',
                                                         5: 'deprivation_4',
                                                         },
                                         },
                        'nation_source': 'EnglandWales',
                        },
    'habitable6_hh': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=HOUSEHOLD&v=DZ21&v=NUMBER_OF_ROOMS_AGG6',
                      'var_map': {'Rooms (Number) - 6 Categories Code': 'habitable',
                                  },
                      'category_map': {'habitable': {1: 'habitable_3_or_less',
                                                     2: 'habitable_4',
                                                     3: 'habitable_5',
                                                     4: 'habitable_6',
                                                     5: 'habitable_7',
                                                     6: 'habitable_8_or_more',
                                                     },
                                       },
                      },
    'carer3_size3_hh': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=HOUSEHOLD&v=DZ21&v=HH_CARERS_TC2&v=HH_SIZE_TC3',
                        'var_map': {'Provision of Unpaid Care (Household) - 3 Categories Code': 'carer',
                                    'Household Size - 3 Categories Code': 'size',
                                    },
                        'category_map': {'carer': {0: 'carer_0',
                                                   1: 'carer_1',
                                                   2: 'carer_2',
                                                   },
                                         'size': {1: 'hh_size_1_2',
                                                  2: 'hh_size_1_2',
                                                  3: 'hh_size_3',
                                                  },
                                         },
                        },
    'cars3_size4_hh': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=HOUSEHOLD&v=DZ21&v=HH_CAR_VAN_TC2&v=HH_SIZE_TC4',
                       'var_map': {'Car or Van Availability - 3 Categories Code': 'cars',
                                   'Household Size - 4 Categories Code': 'size',
                                   },
                       'category_map': {'cars': {0: 'hhcars_0',
                                                 1: 'hhcars_1',
                                                 2: 'hhcars_2',
                                                 },
                                        'size': {1: 'hh_size_1',
                                                 2: 'hh_size_2',
                                                 3: 'hh_size_3',
                                                 4: 'hh_size_4',
                                                 },
                                        },
                       'nation_source': 'EnglandWales',
                       },
    'employed4_size4_hh': {
        'url': 'https://build.nisra.gov.uk/en/custom/data?d=HOUSEHOLD&v=DZ21&v=HH_ADULTS_EMPLOYMENT_TC3&v=HH_SIZE_TC4',
        'var_map': {'Adults in Employment (Household) Code': 'employment',
                    'Household Size - 4 Categories Code': 'size',
                    },
        'category_map': {'employment': {0: 'employed_0',
                                        1: 'employed_1',
                                        2: 'employed_2',
                                        3: 'employed_3',
                                        },
                         'size': {1: 'hh_size_1',
                                  2: 'hh_size_2',
                                  3: 'hh_size_3',
                                  4: 'hh_size_4',
                                  },
                         },
        },
    'type9_hh': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=HOUSEHOLD&v=DZ21&v=HH_FAMILY_COMPOSITION_AGG9',
                 'var_map': {'Household Composition - 9 Categories Code': 'type',
                             },
                 'category_map': {'type': {1: 'one_person_household',
                                           2: 'one_person_household',
                                           3: 'couple_married_civil_no_children',
                                           4: 'couple_married_civil_with_children',
                                           5: 'couple_married_civil_no_children',
                                           6: 'lone_parent_children',
                                           7: 'lone_parent_children',
                                           8: 'other',
                                           9: 'other',
                                           },
                                  },
                 'nation_source': 'EnglandWales',
                 },
    'tenure7_hh': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=HOUSEHOLD&v=DZ21&v=HH_TENURE_AGG7',
                   'var_map': {'Tenure - 7 Categories Code': 'tenure',
                               },
                   'category_map': {'tenure': {1: 'owned_outright',
                                               2: 'owned_mortgage',
                                               3: 'social_rented',
                                               4: 'social_rented',
                                               5: 'private_rented',
                                               6: 'private_rented',
                                               7: 'private_rented',
                                               },
                                    },
                   },
    # 'child2_hh': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=HOUSEHOLD&v=DZ21&v=HH_DEPENDENT_CHILDREN_IND',
    #               'var_map': {'Dependent Children (Household) - 2 Categories Code': 'child',
    #                           },
    #               'category_map': {'child': {0: 'no_children',
    #                                          1: 'with_children',
    #                                          },
    #                                },
    #               },
    'child5A_hh': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=HOUSEHOLD&v=DZ21&v=HH_DEPENDENT_CHILDREN_AGG5A',
                  'var_map': {'Dependent Children (Household) - 5 Categories A Code': 'child',
                              },
                  'category_map': {'child': {1: 'no_children',
                                             2: 'no_children',
                                             3: '00_04',
                                             4: '5_11',
                                             5: '12_18',
                                             },
                                   },
                  },
    # 'tenure7_child2_hh': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=HOUSEHOLD&v=DZ21&v=HH_TENURE_AGG7&v=HH_DEPENDENT_CHILDREN_IND',
    #                       'var_map': {'Tenure - 7 Categories Code': 'tenure',
    #                                   'Dependent Children (Household) - 2 Categories Code': 'child',
    #                                   },
    #                       'category_map': {'tenure': {1: 'owned_outright',
    #                                                   2: 'owned_mortgage',
    #                                                   3: 'social_rented',
    #                                                   4: 'social_rented',
    #                                                   5: 'private_rented',
    #                                                   6: 'private_rented',
    #                                                   7: 'private_rented',
    #                                                   },
    #                                        'child': {0: 'no_children',
    #                                                  1: 'with_children',
    #                                                  },
    #                                        },
    #                       },
    # 'sex2_age11_hrp': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=PEOPLE&v=DZ21&v=HH_REFERENCE_PERSON_IND&v=AGE_BAND_AGG11&v=UR_SEX',
    #                    'var_map': {'Sex Code': 'sex_hrp',
    #                                'Age - 11 Categories Code': 'age_hrp',
    #                                },
    #                    'category_map': {'sex_hrp': {1: 'f',
    #                                                 2: 'm',
    #                                                 },
    #                                     'age_hrp': {1: '00_15',
    #                                                 2: '16_24',
    #                                                 3: '25_34',
    #                                                 4: '25_34',
    #                                                 5: '35_49',
    #                                                 6: '35_49',
    #                                                 7: '35_49',
    #                                                 8: '50_64',
    #                                                 9: '50_64',
    #                                                 10: '50_64',
    #                                                 11: '65_over',
    #                                                 },
    #                                     },
    #                    'hrp': True,
    #                    },
}

### Functions ###
def check_folders_present():
    for p in [RAW_DATA_PATH, OUTPUT_PATH, FINAL_PATH]:
        if not os.path.exists(p):
            os.makedirs(p)


def get_raw_constraint_fullpath(_label):
    fullpath = os.path.join(RAW_DATA_PATH, _label + '.csv')
    return fullpath


def get_processed_constraint_fullpath(_label):
    fullpath = os.path.join(OUTPUT_PATH, 'census2021_' + _label + '.csv')
    return fullpath


def get_raw_constraint_data(_label, _cache=True):
    url = CONSTRAINTS[_label]['url']
    url_corrected = url.replace('data', 'table.csv')
    request_response = requests.get(url_corrected)
    data = pd.read_csv(StringIO(request_response.text))
    if _cache:
        fullpath = get_raw_constraint_fullpath(_label)
        data.to_csv(fullpath, index=False)
    return data


# HR 21/11/25 Get full label for (a) creation of constraints and (b) selection of columns for matching to microdata
def get_constraint_label(_label):
    _dict = CONSTRAINTS[_label]

    category_map = _dict['category_map']
    category_list = list(category_map)

    is_hh_level = _dict.get('hh_level', HH_LEVEL_DEFAULT)
    if is_hh_level:
        _level = 'hh_'
    else:
        _level = 'ind_'
    _label_sequence = '_'.join(category_list)

    label_full = 'data_' + _level + _label_sequence
    return label_full


### Main ###
def main():
    print('\n## Running _02_run_queries... ##')

    # Create data folders
    check_folders_present()

    # Get urban_rural classification - different format to other constraints
    ni_ruc = pd.read_excel(RUC_URL,
                           sheet_name=RUC_SHEET,
                           )
    ni_ruc.to_csv(RUC_RAW, index=False)

    # Retrieve all raw constraints data
    data = {el: get_raw_constraint_data(el) for el in CONSTRAINTS}
    return data


if __name__ == "__main__":
    data = main()
