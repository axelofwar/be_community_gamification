import requests
import pandas as pd
import yaml
import sys
import os

from dotenv import load_dotenv
if "utils" not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    # print("Sys path: ", sys.path)
    from utils import stream_tools as st

# Load the .env file
load_dotenv()


'''
Tools for interacting with the database api - contains functions for:
    - GET request to get the pfp_table from the database
TODO: 
    - add functions for parsing data and doing things with it
    - add functions for writing data to the database if we want to overide the data
    - determine config/env strategy for api inclusion
    - change api endpoint name from api/Tweet to api/PFP_Table
'''

# LOAD AND SET PARAMS
# with open("utils/yamls/params.yml", "r") as f:
#     params = yaml.load(f, Loader=yaml.FullLoader)
params = st.params

database_api = "https://"+params.database_host+params.leaderboard_endpoint
print("DATABASE API: ", database_api)


def get_pfp_table():
    response = requests.get(database_api)
    if response.status_code != 200:
        raise Exception(
            "Cannot get user data (HTTP {}): {}".format(
                response.status_code, response.text)
        )

    output = response.json()
    print("OUTPUT: ", output)
    return output


get_pfp_table()
