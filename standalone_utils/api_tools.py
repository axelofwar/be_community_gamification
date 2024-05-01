import requests
import pandas as pd
import yaml
import sys
import os
import logging
logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv
if "utils" not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from utils import stream_tools as st
else:
    from utils import stream_tools as st
# Load the .env file
load_dotenv()


'''
Tools for interacting with the database api - contains functions for:
    - GET request to get the pfp_table from the database
TODO: 
    - add functions for parsing pfp_table data specifically and doing things with it
    - add functions for writing data to the database if we want to overide the data via api instead of main algo
    - integrate bazel or cmake or other dep management to avoid utils check
'''

params = st.params

database_api = "https://"+params.database_host+params.leaderboard_endpoint
logging.info(f"DATABASE API: {database_api}")


def get_pfp_table():
    """
    Get the PFP Table data from the PostgreSQL database
    """
    response = requests.get(database_api)
    if response.status_code != 200:
        raise Exception(
            "Cannot get user data (HTTP {}): {}".format(
                response.status_code, response.text)
        )

    output = response.json()
    logging.info(f"OUTPUT: {output}")
    return output


get_pfp_table()
