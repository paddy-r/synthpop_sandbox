##### Meta #####
# Author: Hugh Rice
# Version: 1.0
# Date:  2025-09-16
# About: Recode Understanding Society survey data


### Imports ###
from _03_prepare_constraints import *
import src.synthpop_sandbox.usoc_pool_ipf as usoc
from src.synthpop_sandbox.ipf_tools import trs


### Definitions ###
def correct_population_totals(row, domain_map):
    pop = row['population']
    for domain, cols in domain_map.items():
        domain_sum = row[cols].sum()
        if domain_sum != pop:
            # Adjust by rescaling...
            # print('\nTotals before:', pop, domain_sum)
            # print('Before:', row[cols])
            row[cols] = row[cols] * pop / domain_sum
            # ...and then check whether any decimals present: won't be for (e.g.) heating or urban-rural (only two cats)...
            if np.any(np.mod(row[cols], 1) != 0):
                # ...then integerise with TRS algorithm, if decimals present
                row[cols] = trs(row[cols].to_numpy())
            # print('\nAfter:', row[cols])
    return row


### Main ###
def main():
    print('\n## Running _04_recode_setup_survey... ##')


if __name__ == "__main__":
    main()

    ###########################
    ### MICRODATA ALIGNMENT ###
    ###########################

    # 1. Squash tenure-children microdata into two domains
    tc_label = 'data_hh_tenure_child'
    mdata_scot = get_all_microdata()['Scotland']
    tc_cols = [el for el in mdata_scot.columns if el.startswith(tc_label)]

    tenure_cats = tuple(set(CONSTRAINTS['tenure7_hh']['category_map']['tenure'].values()))
    child_cats = tuple(set(CONSTRAINTS['child5A_hh']['category_map']['child'].values()))

    tenure_cols = {'data_hh_tenure%' + cat: [el for el in tc_cols if cat in el] for cat in tenure_cats}
    child_cols = {'data_hh_child%' + cat: [el for el in tc_cols if cat in el] for cat in child_cats}

    mdata_new = pd.DataFrame(index=mdata_scot.index)  # Subset on Scotland households only
    grouped_cols = tenure_cols | child_cols
    for new_col, old_cols in grouped_cols.items():
        mdata_new[new_col] = mdata_scot[old_cols].sum(axis=1)


    # 2. Get number of habitable rooms from US and add to microdata
    year = 2023
    prefix = usoc.get_wave_letter(year) + '_'
    hhdata_all = usoc.get_us_data(year, group='hhresp')
    _vars = ['hidp', 'hsbeds', 'hsrooms']

    cols_to_grab = [prefix + el for el in _vars]
    hhdata = hhdata_all[cols_to_grab].copy()
    hhdata.columns = [el.lstrip(prefix) for el in hhdata.columns]
    hhdata.set_index('hidp', inplace=True)

    hhdata['habitable_raw'] = hhdata['hsbeds'] + hhdata['hsrooms']  # Create the new domain (not present for EW or S)

    # Recoding
    label = 'data_hh_habitable%'
    hhdata.loc[(hhdata['habitable_raw'] >= 0) & (hhdata['habitable_raw'] <= 3), 'habitable'] = 'habitable_3_or_less'
    hhdata.loc[(hhdata['habitable_raw'] == 4), 'habitable'] = 'habitable_4'
    hhdata.loc[(hhdata['habitable_raw'] == 5), 'habitable'] = 'habitable_5'
    hhdata.loc[(hhdata['habitable_raw'] == 6), 'habitable'] = 'habitable_6'
    hhdata.loc[(hhdata['habitable_raw'] == 7), 'habitable'] = 'habitable_7'
    hhdata.loc[(hhdata['habitable_raw'] >= 8), 'habitable'] = 'habitable_8_or_more'
    hhdata.drop(columns=['hsbeds', 'hsrooms', 'habitable_raw'], inplace=True)

    # One-hot encoding - Pandas function is "get_dummies"
    hhdata_onehot = pd.get_dummies(hhdata, prefix='data_hh_habitable%', prefix_sep='').astype(int)

    # Merge all NI-specific extra microdata to be merged with existing from EW and S
    mdata_new = mdata_new.merge(hhdata_onehot, left_index=True, right_index=True)
    mdata_new = mdata_new.sort_index(axis=1)  # Sort columns

    # Get existing microdata and merge new domains
    mdata_path = get_microdata_outpath()
    mdata_old = pd.read_csv(mdata_path).set_index('id')
    mdata_final = mdata_old.merge(mdata_new, left_index=True, right_index=True)


    #############################
    ### CONSTRAINTS ALIGNMENT ###
    #############################

    # Get existing constraints data
    condata_path = get_constraints_outpath()
    condata_final = pd.read_csv(condata_path).set_index('areacode')

    # Specify additional NI-specific constraints data
    constraints_to_add = ['tenure7_hh', 'child5A_hh', 'habitable6_hh']

    # Combine both sets of constraints data; must match new microdata set
    for label in constraints_to_add:
        con_path = get_processed_constraint_fullpath(label)
        condata = pd.read_csv(con_path).set_index('areacode')
        condata_final = condata_final.merge(condata, left_index=True, right_index=True)

    # Complete-case analysis with diagnostic output
    areas_missing = condata_final.loc[condata_final.isnull().any(axis=1)].copy()
    n_areas = len(areas_missing)
    condata_final.drop(areas_missing.index, inplace=True)

    print('\n### Complete-case analysis of constraints data ###')
    print('Number of areas with any missing data: {}'.format(n_areas))
    print('Removed from constraints data')

    # Lastly, correct totals by proportional adjustment (actually TRS)
    # cdata = pd.read_csv(get_constraints_outpath()).set_index('areacode')
    hh_cols = [el for el in condata_final.columns if el.startswith('data_hh')]
    hh_domains = set([el.split('%')[0] for el in hh_cols])
    domain_dict = {d: [el for el in hh_cols if el.startswith(d)] for d in hh_domains}

    print('\n ### Running proportional adjustment to match domain totals to population totals... ###')
    condata_final = condata_final.apply(correct_population_totals, domain_map=domain_dict, axis=1)
    print('Done!')


    ###########################
    ### DUMP ALL FINAL DATA ###
    ###########################

    # Sort both datasets
    column_to_move = condata_final.pop('population')
    condata_final = condata_final.sort_index(axis=1)
    condata_final.insert(0, 'population', column_to_move)
    mdata_final = mdata_final.sort_index(axis=1)

    # (Re)dump data to final and SA folders
    condata_path = get_constraints_outpath()
    mdata_path = get_microdata_outpath()
    condata_final.to_csv(condata_path)
    mdata_final.to_csv(mdata_path)

    condata_path_sa = get_constraints_outpath_compass()
    mdata_path_sa = get_microdata_outpath_compass()
    condata_final.to_csv(condata_path_sa)
    mdata_final.to_csv(mdata_path_sa)
