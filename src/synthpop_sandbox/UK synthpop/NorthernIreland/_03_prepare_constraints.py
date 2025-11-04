##### Meta #####
# Author: Hugh Rice
# Version: 1.0
# Date:  2025-09-16
# About: Prepare constraints from small-area census data


### Imports ###
import pandas as pd
from _02_run_queries import *


### Definitions ###


def process_population_data(_cache=True):
    pop_data = {}
    for _pop, _dict in POP_DICT.items():
        data = pd.read_excel(_dict['file'],
                             sheet_name=_dict['sheet'],
                             header=_dict['header_row'],
                             )
        var_map = _dict['var_map']
        data = data[list(var_map)].rename(columns=var_map)

        if _cache:
            cache_full = _dict['outfile']
            data.to_csv(cache_full, index=False)
        pop_data[_pop] = data
    return pop_data


def process_urban_rural_data(pop_hh):
    # Standardise urban-rural classification
    ruc_raw = pd.read_csv(RUC_RAW)
    ruc_hh = ruc_raw[list(RUC_VAR_MAP)].rename(columns=RUC_VAR_MAP)

    ruc = pop_hh.merge(ruc_hh, on='areacode')
    ruc['urban_status'] = ruc['urban_status'] == 'Urban'
    ruc['urban_status'] = ruc['urban_status'].astype(int)

    # Farm out each binary value to new columns and drop old one
    ruc['urban'] = ruc['number'] * ruc['urban_status']
    ruc['rural'] = ruc['number'] * (1 - ruc['urban_status'])
    ruc = ruc.drop(columns=['number', 'urban_status']).set_index('areacode')
    ruc.columns = ['data_hh_urban_rural%' + el for el in ruc.columns]

    ruc.to_csv(RUC_OUT)
    return ruc


def process_constraint_data(_label, _cache_path=RAW_DATA_PATH, cache=True):
    _dict = CONSTRAINTS[_label]
    _cache_fullpath = get_raw_constraint_fullpath(_label)
    raw = pd.read_csv(_cache_fullpath)

    # Filter for correct HRP indicator value
    is_hrp = _dict.get('hrp', HRP_DEFAULT)
    if is_hrp:
        hrp_col = HRP_COL_DEFAULT
        raw = raw.loc[raw[hrp_col] == 1]
        raw.drop(columns=HRP_HEADERS, inplace=True)

    areacode_col = _dict.get('areacode_col', AREACODE_COL_DEFAULT)
    count_col = _dict.get('count_col', COUNT_COL_DEFAULT)
    var_map = {areacode_col: AREACODE_DEFAULT, count_col: COUNT_DEFAULT} | _dict['var_map']
    raw = raw.rename(columns=var_map)
    processed = raw[list(var_map.values())].copy()  # Copying avoids Pandas warnings

    category_map = _dict['category_map']
    category_list = list(category_map)
    for _var, _map in category_map.items():
        processed[_var] = processed[_var].map(_map)

    processed = processed.pivot_table(index=AREACODE_DEFAULT,
                                      columns=list(category_map),
                                      values=COUNT_DEFAULT,
                                      aggfunc='sum')  # Must specify sum as default is mean => very wrong

    is_hh_level = _dict.get('hh_level', HH_LEVEL_DEFAULT)
    if is_hh_level:
        _level = 'hh_'
    else:
        _level = 'ind_'
    _label_sequence = '_'.join(category_list)
    full_label = 'data_' + _level + _label_sequence + LABEL_JOINER
    if len(category_list) > 1:  # Accounts for multivariate constraints
        processed.columns = processed.columns.map('_'.join)
    processed.columns = [full_label + el for el in processed.columns]

    if cache:
        print('Caching to file')
        _processed_fullpath = get_processed_constraint_fullpath(_label)
        processed.to_csv(_processed_fullpath)

    return processed


### Main ###
def main(_labels=CONSTRAINTS):
    print('\n## Running 03_prepare_constraints... ##')

    # Prepare population data by DZ
    pop_data = process_population_data()
    pop_hh = pop_data['hh']

    # Get rural-urban classification master constraint data
    ruc_data = process_urban_rural_data(pop_hh)

    # Process constraint set
    # constraint_set = CONSTRAINTS
    constraint_set = [
        'sex2_age11_ind',      # Ind multivariate
        'ethnicity13_ind',     # Ind univariate
        'qual8_ind',           # Ind univariate
        'centralheating2_hh',  # HH univariate
        'deprivation5_hh',     # HH Univariate
        'employed4size4_hh',   # HH multivariate
        # 'sex2_age11_hrp',      # HH multivariate
    ]

    data = {}
    for _label in constraint_set:
        try:
            data[_label] = process_constraint_data(_label)
            print('Done for constraint:', _label)
        except Exception as e:
            print(e)
            print("Couldn't do constraint:", _label)

    # data = {l: process_constraint_data(l) for l in _labels}
    return ruc_data, data


if __name__ == "__main__":

    # Get constraints data
    ruc_data, data = main()

    # Begin master constraint table construction: stem and RUC master constraint...
    stem = pd.DataFrame(index=ruc_data.index)  # Get master set of Data Zones from RUC data, as no empty cells
    stem['population'] = ruc_data.sum(axis=1)  # Just grab total hh population from sum of urban-rural master constraint
    constraints = stem.merge(ruc_data, how='left', on='areacode')

    # ...then merge individual constraints
    for _label, _dataset in data.items():
        constraints = constraints.merge(_dataset, how='left', on='areacode')

    # Now must grab all available US pool data (Scotland + EW)...
    scot_pool_fullpath = os.path.join(SCOTLAND_PATH, 'us_hh_export_go.csv')
    scot_pool = pd.read_csv(scot_pool_fullpath).set_index('id')
    ew_pool_fullpath = os.path.join(ENGLAND_WALES_PATH, 'us_hh_export_go.csv')
    ew_pool = pd.read_csv(ew_pool_fullpath).set_index('id')

    # Merge S and EW data to maximise number of constraints data
    cols_to_merge = list(set(ew_pool.columns) - set(scot_pool.columns))  # Columns only in EW data
    gb_pool = pd.merge(scot_pool, ew_pool[cols_to_merge], left_index=True, right_index=True, how='outer')

    # ...then subset constraints and make sure order is correct by sorting both
    gb_pool.columns = [el.replace('age_sex', 'sex_age') for el in gb_pool.columns]  # Age-sex order in headers is wrong!
    common_columns = list(set(constraints.columns) & set(gb_pool.columns))
    gb_pool = gb_pool[common_columns]

    # Remove anyextraneous columns present in GB data not present in constraints
    missing_columns = list(set(constraints.columns) - set(gb_pool.columns) - {'population'})
    # gb_pool.loc[:, missing_columns] = 0  # Option 1: Create missing columns and fill with zeroes, to agree with NI constraints columns
    constraints.drop(columns=missing_columns, axis=1, inplace=True)  # Option 2: Remove those missing columns from constraints table

    gb_pool.sort_index(axis=1, inplace=True)
    constraints.sort_index(axis=1, inplace=True)
    column_to_move = constraints.pop('population')
    constraints.insert(0, 'population', column_to_move)

    # Dump constraints and subsetted US pool data; names are given in UK808 config file, config_ni.json
    constraints_file = 'census2021_ni_go.csv'
    pool_file = 'us_hh_export_ni_go.csv'
    constraints_fullpath = os.path.join(FINAL_PATH, constraints_file)
    constraints_fullpath_synthpop = os.path.join(COMPASS_PATH, 'data', 'Northern Ireland', constraints_file)
    pool_fullpath = os.path.join(FINAL_PATH, pool_file)
    pool_fullpath_synthpop = os.path.join(COMPASS_PATH, 'data', 'Northern Ireland', pool_file)

    constraints.to_csv(constraints_fullpath)
    constraints.to_csv(constraints_fullpath_synthpop)
    gb_pool.to_csv(pool_fullpath)
    gb_pool.to_csv(pool_fullpath_synthpop)
