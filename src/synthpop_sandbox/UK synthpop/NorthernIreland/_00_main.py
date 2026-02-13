##### Meta #####
# Author: Hugh Rice
# Version: 1.0
# Date:  2025-09-16
# About: The Main Control File


### Imports ###
import os
from os.path import dirname as up
import subprocess
import time


### Main ###
def main(_path):
    print('\n## Running _00_main... ##')

    scripts = ['_02_run_queries.py',
               '_03_prepare_constraints.py',
               '_04_recode_setup_survey.py',
               '_05_create_synthpop.py'
               ]
    for s in scripts:
        script_fullpath = os.path.join(_path, s)
        subprocess.call(["python", script_fullpath])


### Run everything ###
if __name__ == "__main__":

    # Benchmark run time: START
    time_start = time.time()

    # Run all code
    _path = up(os.path.abspath(__file__))
    main(_path)

    # Benchmark run time: END
    time_end = time.time()
    time_elapsed = time_end - time_start
    print('\nElapsed time = {}'.format(time_elapsed))
