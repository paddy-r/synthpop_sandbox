##### Meta #####
# Author: Hugh Rice
# Version: 1.0
# Date:  2025-09-16
# About: Any utility functions


### Imports ###
import os
from os.path import dirname as up
import geopandas as gpd


### Definitions ###
NI_PATH = up(__file__)
RAW_DATA_PATH = os.path.join(NI_PATH, 'data')
PERSISTENT_DATA_PATH = os.path.join(NI_PATH, 'persistent_data')
OUTPUT_PATH = os.path.join(NI_PATH, 'constraints')
FINAL_PATH = os.path.join(NI_PATH, 'final')

# Paths to simulated annealing package, UK808
HOME_PATH = os.path.expanduser("~")
# UK808_PATH = os.path.join(HOME_PATH, 'data', 'UK808-0610v2')
COMPASS_PATH = os.path.join(HOME_PATH, 'data', 'compass')  # HR 30/10/25 Updated to Compass path
SCOTLAND_PATH = os.path.join(HOME_PATH, 'data', '_From UK synthpop', 'Scotland')  # HR 31/10/25 Microdata and US from Scotland synthpop

# Spatial stuff
GEOJSON_NI = ''
POP_CENTROIDS_NI = ''


### Utility functions ###
print('Importing utility functions...')


# HR 06/11/25 Grab NI spatial boundaries for mapping/visualisation
def get_spatial_boundaries_ni():
    boundaries = ''
    return boundaries

def get_population_centroids_ni():
    centroids = ''
    return centroids


if __name__ == "__main__":
    b = get_spatial_boundaries_ni()
    c = get_population_centroids_ni()
