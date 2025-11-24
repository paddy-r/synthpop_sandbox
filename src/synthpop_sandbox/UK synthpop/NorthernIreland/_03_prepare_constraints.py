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

    full_label = get_constraint_label(_label) + LABEL_JOINER

    if len(category_list) > 1:  # Accounts for multivariate constraints
        processed.columns = processed.columns.map(VARIABLE_JOINER.join)
    processed.columns = [full_label + el for el in processed.columns]

    if cache:
        # print('Caching to file')
        _processed_fullpath = get_processed_constraint_fullpath(_label)
        processed.to_csv(_processed_fullpath)

    return processed


### Main ###
def main(_labels=CONSTRAINTS):
    print('\n## Running _03_prepare_constraints... ##')

    # Prepare population data by DZ
    pop_data = process_population_data()
    pop_hh = pop_data['hh']

    # Get rural-urban classification master constraint data
    ruc_data = process_urban_rural_data(pop_hh)

    # Process constraint set
    constraint_set = CONSTRAINTS
    # constraint_set = [
    #     'sex2_age11_ind',      # Ind multi
    #     'qual8_ind',           # Ind uni
    #     'ethnicity13_ind',     # Ind uni
    #     'marital6_ind',        # Ind uni
    #     'health5_ind',         # Ind uni
    #     'activity12_ind',      # Ind uni
    #     'centralheating2_hh',  # HH uni
    #     'deprivation5_hh',     # HH uni
    #     'carer3_size3_hh',     # HH multi
    #     'cars3_size4_hh',      # HH multi
    #     'employed4_size4_hh',  # HH multi
    #     'type9_hh',            # HH uni
    #     # 'tenure7_child2_hh'    # HH uni  # EXCLUDE: Only 50% coverage
    #     # 'sex2_age11_hrp',      # HH multi  # EXCLUDE: HRP data not used in EW or S so far
    # ]

    data = {}
    for _label in constraint_set:
        try:
            data[_label] = process_constraint_data(_label)
            print('Done for constraint:', _label)
        except Exception as e:
            print(e)
            print("Couldn't do constraint:", _label)
            pass

    return ruc_data, data


if __name__ == "__main__":

    # Get constraints data
    ruc_data, data = main()

    # Begin master constraint table construction: stem and RUC master constraint...
    stem = pd.DataFrame(index=ruc_data.index)  # Get master set of Data Zones from RUC data, as no empty cells
    stem['population'] = ruc_data.sum(axis=1)  # Just grab total hh population from sum of urban-rural master constraint
    constraints = stem.merge(ruc_data, how='left', on='areacode')

    # ...then merge individual constraints into single dataset
    for _label, _dataset in data.items():
        constraints = constraints.merge(_dataset, how='left', on='areacode')

    # Grab all microdata...
    mdata_lookup = get_all_microdata()
    mdata_lookup = fix_microdata_age_sex(mdata_lookup)
    mdata = pd.DataFrame(index=mdata_lookup['Scotland'].index)

    # ...then retain only microdata present in constraints data, filling in empty columns as necessary
    for constraint, cdata in data.items():

        nation_source = CONSTRAINTS[constraint].get('nation_source', NATION_SOURCE_DEFAULT)
        full_label = get_constraint_label(constraint) + LABEL_JOINER
        constraint_cols = [el for el in cdata.columns if el.startswith(full_label)]

        mdata_raw = mdata_lookup[nation_source]
        mdata_cols = [el for el in mdata_raw.columns if el.startswith(full_label)]

        cols_present = set(constraint_cols) & set(mdata_cols)
        cols_missing = set(constraint_cols) - set(mdata_cols)

        # Check if ANY microdata columns present; if so, fill any missing columns with zero
        # If NO COLUMNS present, assume constraint not properly configured and ignore
        if len(cols_present) == 0:
            print('No microdata for {}; skipping'.format(constraint))
            continue

        if len(cols_missing) == 0:
            print('Complete microdata for {}; adding to final dataset'.format(constraint))
            mdata = mdata.merge(mdata_raw[list(cols_present)], left_index=True, right_index=True)

        elif len(cols_missing) > 0:
            print('Some missing columns for {}; filling in with zeroes'.format(constraint))
            mdata = mdata.merge(mdata_raw[list(cols_present)], left_index=True, right_index=True)
            mdata.loc[:, list(cols_missing)] = 0

    # Finally, remove any constraints data not present in microdata and sort both datasets
    column_to_move = constraints.pop('population')
    constraints = constraints[mdata.columns]
    constraints = constraints.sort_index(axis=1)
    constraints.insert(0, 'population', column_to_move)
    mdata = mdata.sort_index(axis=1)

    # Dump constraints and subsetted microdata; names are given in SA config file, config_ni.json
    constraints_file = 'census2021_ni_go.csv'
    mdata_file = 'us_hh_export_ni_go.csv'
    constraints_fullpath = os.path.join(FINAL_PATH, constraints_file)
    constraints_fullpath_synthpop = os.path.join(COMPASS_PATH, 'data', 'Northern Ireland', constraints_file)
    mdata_fullpath = os.path.join(FINAL_PATH, mdata_file)
    mdata_fullpath_synthpop = os.path.join(COMPASS_PATH, 'data', 'Northern Ireland', mdata_file)

    constraints.to_csv(constraints_fullpath)
    constraints.to_csv(constraints_fullpath_synthpop)
    mdata.to_csv(mdata_fullpath)
    mdata.to_csv(mdata_fullpath_synthpop)
