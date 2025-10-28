##### Meta #####
# Author: Hugh Rice
# Version: 1.0
# Date:  2025-09-16
# About: Create synthetic population - calls Go code


### Imports ###
import subprocess
from _02_run_queries import *


### Definitions ###
# CONFIG_FILE = 'config.json'  # Default (Scotland) config - for testing
CONFIG_FILE = 'config_ni.json'  # NI config
# CONFIG_FILE = 'config_ni_test.json'  # NI config with reduced columns for testing


### Main ###
def main():
    print('\n## Running 05_create_synthpop... ##')
    previous_wd = os.getcwd()
    os.chdir(UK808_PATH)
    exe_file = 'uk-808-gui'
    fullargs = ' '.join(['./' + exe_file, '-c', '-f', CONFIG_FILE])  # NI version
    print('Running UK-808 via cmd:', fullargs)
    subprocess.run(fullargs, shell=True)
    os.chdir(previous_wd)


if __name__ == "__main__":
    main()
