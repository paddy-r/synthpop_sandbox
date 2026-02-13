# HR 03/05/25 To try and create pool population from Understanding Society by category combinations
# Parameters are:
# (a) Number of constraints to use to define categories, working backwards from least important to most
# (b) Number of years of US data from which to draw pool pop
# Other things to consider:
# - How to account for individuals in multiple years: reset pidp, then lookup key will be new_pipp -> (pidp, year)
# - Order of constraints (most important first):
#   - age-sex, ethnicity, hh_tenure, hh_composition
# - Range of years: start with 1, 3, 5...
# - Latest US data (which we have) is Wave M/14, Jan 22-May 24

import os
from string import ascii_lowercase as alphabet

import pandas as pd

YEAR_REF = 2020
YEARS_DELTA = 2  # How many years around reference year to draw individuals from; max possible is 4 with Wave M/14/2023
HOME_PATH = os.path.expanduser("~")
# US_PATH = os.path.join(HOME_PATH, 'data', 'understanding_society', 'UKDA-6614-stata', 'stata', 'stata13_se', 'ukhls')
US_PATH = os.path.join(HOME_PATH, 'data', 'UKDA-6614-stata', 'stata', 'stata13_se', 'ukhls')

# Translate raw US variable names into SIPHER synthpop constraint-friendly names
PERSISTENT_VARS = {'pidp': 'pidp'}
YEAR_VARS = {
    'hidp': 'hidp',
    'age_dv': 'age',
    'sex': 'sex',
    'racel_dv': 'ethnicity',
    'hiqual_dv': 'qualification',
    'marstat': 'marital',
    'jbstat': 'economic',
    'scsf1': 'general_health',
    'hhtype_dv': 'hh_composition',
    # 'tenure_dv': 'hh_tenure',
}

PERSISTENT_VARS_HH = {}
YEAR_VARS_HH = {
    # 'hhtype_dv': 'hh_composition',
    'tenure_dv': 'hh_tenure',
}

VAR_GROUPS_DEFAULT = (PERSISTENT_VARS, YEAR_VARS, PERSISTENT_VARS_HH, YEAR_VARS_HH)


def get_wave_letter(year):
    wave_number = year - 2010
    wave_letter = alphabet[wave_number]
    return wave_letter


def get_us_data(year, group):
    year_prefix = get_wave_letter(year)
    file_name = year_prefix + '_' + group + '.dta'
    file_full = os.path.join(US_PATH, file_name)
    return pd.read_stata(file_full, convert_categoricals=False)


if __name__ == "__main__":

    # # Testing: load US raw data
    # years = list(range(YEAR_REF - YEARS_DELTA, YEAR_REF + YEARS_DELTA + 1))
    # y = 2020
    # pop = pd.DataFrame()
    #
    # for y in sorted(years):
    #     di = get_us_data(y, 'indresp')
    #     dh = get_us_data(y, 'hhresp')
    #
    #     wave_letter = get_wave_letter(y)
    #     merge_key = wave_letter + '_hidp'
    #
    #     dh.drop(columns=wave_letter + '_' + 'hhtype_dv', inplace=True)  # Present in both! Fix properly later
    #     m = di.merge(dh, on=merge_key, how='left')
    #
    #     # Get variable names and filter data
    #     vars_persistent = PERSISTENT_VARS | PERSISTENT_VARS_HH
    #     vars_noprefix = YEAR_VARS | YEAR_VARS_HH
    #     vars_prefix = {wave_letter + '_' + k: v for k, v in vars_noprefix.items()}
    #     vars_to_filter = vars_persistent | vars_prefix
    #
    #     filtered = m[vars_to_filter.keys()]
    #     f = filtered.rename(columns=vars_to_filter)
    #     f.insert(2, 'year', y)
    #
    #     pop = pd.concat([pop, f])

    letter = get_wave_letter(2023)
    hhdata = get_us_data(2023, group='hhresp')
