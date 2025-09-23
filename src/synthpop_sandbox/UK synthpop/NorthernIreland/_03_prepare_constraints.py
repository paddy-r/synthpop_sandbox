##### Meta #####
# Author: Hugh Rice
# Version: 1.0
# Date:  2025-09-16
# About: Prepare constraints from small-area census data


### Imports ###
import pandas as pd
from _02_run_queries import *


### Definitions ###
POP_VAR_MAP = {'Geography code': 'areacode',
               'All households': 'number',
               }
RUC_VAR_MAP = {'DZ2021_code': 'areacode',
               'Urban_status': 'urban_status',
               }
RUC_URBAN = 'Urban'  # Binary identifier; other is
RUC_OUT = os.path.join(OUTPUT_PATH, 'census2021_c1_urbanrural_master.csv')


def get_raw_constraint_data(_label, _cache_path=RAW_DATA_PATH, cache=True):
    _dict = CONSTRAINTS[_label]
    url = _dict['url']
    _cache_pathfull = os.path.join(_cache_path, _label + '.csv')

    try:
        print('Trying to get raw constraint data for {} from cache...'.format(_label))
        processed = pd.read_csv(_cache_pathfull)
        print('Found it!')
        return processed
    except:
        pass

    print('Failed, retrieving from web...')
    raw = get_data_from_url(url)
    print('Done!')

    # Filter for correct HRP indicator value
    is_hrp = _dict.get('hrp', HRP_DEFAULT)
    if is_hrp:
        hrp_col = HRP_COL_DEFAULT
        raw = raw.loc[raw[hrp_col] == 1]

    areacode_col = _dict.get('areacode_col', AREACODE_COL_DEFAULT)
    count_col = _dict.get('count_col', COUNT_COL_DEFAULT)
    var_cols = _dict['var_cols']
    var_labels = _dict['var_labels']
    processed = raw[[areacode_col, count_col] + var_cols].copy()

    # Standardise column headers
    _map = {areacode_col: AREACODE_DEFAULT, count_col: COUNT_DEFAULT} | dict(zip(var_cols, var_labels))
    processed.rename(columns=_map, inplace=True)

    # Combine multivariate columns
    if len(var_cols) > 1:
        combi_col = VAR_SEPARATOR.join(var_labels)
        processed[combi_col] = processed[var_labels].astype(str).agg(VAR_SEPARATOR.join, axis=1)
        processed.drop(columns=var_labels, inplace=True)

    if cache:
        print('Caching to file')
        processed.to_csv(_cache_pathfull, index=False)

    return processed


### Main ###
def main(_labels=CONSTRAINTS):
    print('\n## Running 03_prepare_constraints... ##')

    # Standardise urban-rural classification
    ruc_raw = pd.read_csv(NI_RUC_RAW)
    pop_raw = pd.read_csv(NI_POP_RAW)

    ruc_standard = ruc_raw[list(RUC_VAR_MAP)].rename(columns=RUC_VAR_MAP)
    pop_standard = pop_raw[list(POP_VAR_MAP)].rename(columns=POP_VAR_MAP)

    ruc = pop_standard.merge(ruc_standard, on='areacode')
    ruc['urban_status'] = ruc['urban_status'] == 'Urban'
    ruc['urban_status'] = ruc['urban_status'].astype(int)

    # Farm out each binary value to new columns and drop old one
    ruc['urban'] = ruc['number'] * ruc['urban_status']
    ruc['rural'] = ruc['number'] * (1 - ruc['urban_status'])
    ruc.drop(columns=['number', 'urban_status'], inplace=True)

    ruc.to_csv(RUC_OUT, index=False)

    # Cycle over all other (i.e. not urban-rural) constraints
    data = {l: get_raw_constraint_data(l) for l in _labels}
    return data


if __name__ == "__main__":
    data = main()
