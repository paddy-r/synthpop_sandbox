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


### Definitions ###
NI_PATH = up(__file__)
RAW_DATA_PATH = os.path.join(NI_PATH, 'data')
OUTPUT_PATH = os.path.join(NI_PATH, 'constraints')

# Urban-rural classification (RUC)
NI_RUC_URL = "https://www.nisra.gov.uk/sites/nisra.gov.uk/files/publications/geography-data-zone-and-super-data-zone-lookups.xlsx"
NI_RUC_SHEET = "DZ21_Urban_mixed_rural_lookup"
NI_RUC_RAW = os.path.join(RAW_DATA_PATH, 'ni_ruc_raw.csv')

NI_POP_FILE = os.path.join(RAW_DATA_PATH, "census-2021-ms-e01.xlsx")
NI_POP_SHEET = "DZ"
NI_POP_HEADER = 5
NI_POP_RAW = os.path.join(RAW_DATA_PATH, 'ni_pop_raw.csv')

AREACODE_COL_DEFAULT = 'Census 2021 Data Zone Code'
AREACODE_DEFAULT = 'areacode'
COUNT_COL_DEFAULT = 'Count'
COUNT_DEFAULT = 'count'
IND_LEVEL_DEFAULT = True
HRP_DEFAULT = False
HRP_COL_DEFAULT = 'Household Reference Person Indicator Code'
VAR_SEPARATOR = '__'

# Constraints data dictionary
CONSTRAINTS = {'highestqual8_ind': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=PEOPLE&v=DZ21&v=HIGHEST_QUALIFICATION',
                                    'var_cols': ['Qualifications (Highest Level) Code',
                                                 ],
                                    'var_labels': ['qual8_ind',
                                                   ],
                                    'ind_level': True,
                                    },
               'age8_sex2_ind': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=PEOPLE&v=DZ21&v=AGE_BAND_AGG8&v=UR_SEX',
                                 'var_cols': ['Age - 8 Categories Code',
                                              'Sex Code',
                                              ],
                                 'var_labels': ['age8_ind',
                                                'sex2_ind',
                                                ],
                                 'ind_level': True,
                                 },
               'tenure7_hh': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=HOUSEHOLD&v=DZ21&v=HH_TENURE_AGG7',
                              'var_cols': ['Tenure - 7 Categories Code',
                                           ],
                              'var_labels': ['tenure7_hh',
                                             ]
                              },
               'age8_sex2_hrp': {'url': 'https://build.nisra.gov.uk/en/custom/data?d=PEOPLE&v=DZ21&v=HH_REFERENCE_PERSON_IND&v=AGE_BAND_AGG8&v=UR_SEX',
                                 'var_cols': ['Age - 8 Categories Code',
                                              'Sex Code',
                                              ],
                                 'var_labels': ['age8_hrp',
                                                'sex2_hrp',
                                                ],
                                 'hrp': True,
                                 },
               }


### Functions ###
def check_folders_present():
    for p in [RAW_DATA_PATH, OUTPUT_PATH]:
        if not os.path.exists(p):
            os.makedirs(p)


def get_data_from_url(url):
    url_corrected = url.replace('data', 'table.csv')
    request_response = requests.get(url_corrected)
    data = pd.read_csv(StringIO(request_response.text))
    return data


### Main ###
def main():
    print('\n## Running 02_run_queries... ##')

    # Create data folders
    check_folders_present()

    # Get urban_rural classification
    ni_ruc = pd.read_excel(NI_RUC_URL,
                           sheet_name=NI_RUC_SHEET,
                           )
    ni_ruc.to_csv(NI_RUC_RAW, index=False)

    ni_pop = pd.read_excel(NI_POP_FILE,
                           sheet_name=NI_POP_SHEET,
                           header=NI_POP_HEADER,
                           )
    ni_pop.to_csv(NI_POP_RAW, index=False)


if __name__ == "__main__":
    main()

