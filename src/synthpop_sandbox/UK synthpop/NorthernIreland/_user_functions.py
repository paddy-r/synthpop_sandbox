##### Meta #####
# Author: Hugh Rice
# Version: 1.0
# Date:  2025-09-16
# About: Any utility functions


### Imports ###
import os
from os.path import dirname as up
import pandas as pd
import geopandas as gpd
from torch.utils.collect_env import get_os

### Definitions ###
NI_PATH = up(__file__)
RAW_DATA_PATH = os.path.join(NI_PATH, 'data')
PERSISTENT_DATA_PATH = os.path.join(NI_PATH, 'persistent_data')
OUTPUT_PATH = os.path.join(NI_PATH, 'constraints')
FINAL_PATH = os.path.join(NI_PATH, 'final')

# Paths to simulated annealing package
HOME_PATH = os.path.expanduser("~")
# UK808_PATH = os.path.join(HOME_PATH, 'data', 'UK808-0610v2')
COMPASS_PATH = os.path.join(HOME_PATH, 'data', 'compass')  # HR 30/10/25 Updated to Compass path
UK_PATH = os.path.join(HOME_PATH, 'data', '_From UK synthpop')  # HR 03/11/25 Path to UK synthpop, for grabbing EW and S data
ENGLAND_WALES_PATH = os.path.join(UK_PATH, 'England and Wales')  # HR 03/11/25 Microdata and US from EW synthpop
SCOTLAND_PATH = os.path.join(UK_PATH, 'Scotland')  # HR 31/10/25 Microdata and US from Scotland synthpop
ALL_UK_PATH = os.path.join(UK_PATH, 'All UK')  # HR 21/11/25 Microdata and US for all-UK

# Lookup for microdata files
MICRODATA_LOOKUP = {
    'EnglandWales': os.path.join(ENGLAND_WALES_PATH, 'us_hh_export_go.csv'),
    'Scotland': os.path.join(SCOTLAND_PATH, 'us_hh_export_go.csv'),
    # 'AllUK': os.path.join(ALL_UK_PATH, 'us_hh_export_go.csv'),  # Placeholder - doesn't exist yet
}

# Spatial stuff
GEOJSON_NI = os.path.join(PERSISTENT_DATA_PATH, 'DZ2021.geojson')
POP_CENTROIDS_NI = os.path.join(PERSISTENT_DATA_PATH, 'census-2021-population-weighted-centroids-data-zone.csv')


### Utility functions ###process_pop
print('Importing utility functions...')


# HR 06/11/25 Grab NI spatial boundaries for mapping/visualisation
def get_spatial_boundaries_ni(file_fullpath=GEOJSON_NI):
    boundaries = gpd.read_file(file_fullpath)
    return boundaries

def get_population_centroids_ni(file_fullpath=POP_CENTROIDS_NI):
    centroids = pd.read_csv(file_fullpath)
    return centroids

def merge_boundaries_centroids_ni(boundaries=None, centroids=None):
    if boundaries is None:
        boundaries = get_spatial_boundaries_ni()
    if centroids is None:
        centroids = get_population_centroids_ni()

    centroids.rename(columns={'DZ2021_code': 'DZ2021_cd', 'DZ2021_name': 'DZ2021_nm', 'X': 'centroid_x', 'Y': 'centroid_y'}, inplace=True)
    centroids.drop(columns=['DZ2021_nm'], inplace=True)

    merge_key = 'DZ2021_cd'
    merged = boundaries.merge(centroids, on=merge_key)
    return merged


if __name__ == "__main__":
    # m = merge_boundaries_centroids_ni()  # Testing retrieval and merging of all spatial data
    pass
