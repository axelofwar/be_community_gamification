from dotenv import load_dotenv
import json
import os
import requests
import pandas as pd
import sys

if "utils" not in sys.path:
    sys.path.append(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))
    from utils import stream_tools as st

if 'GITHUB_ACTION' not in os.environ:
    load_dotenv()

'''
Tools for interacting with the Twitter API in a filtered stream - contains functions for:
    - Setting up the bearer token
    - Getting the username of a tweet author by their author id
    - Getting the rules from the rules.yml file
    - Adding rules to the rules.yml file
    - Removing rules from the rules.yml file
    - Updating the rules on the Twitter API
'''


bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
params = st.params


# SET BEARER TOKEN AUTH
def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FilteredStreamPython"
    return r


# GET RULES OF CURRENT STREAM
def get_rules():
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(
                response.status_code, response.text)
        )
    print(json.dumps(response.json()))
    return response.json()


# DELETE CURRENT SET STREAM SET RULES
def delete_all_rules(rules):
    if rules is None or "data" not in rules:
        return None

    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot delete rules (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    print(json.dumps(response.json()))


# SET CURRENT STREAM RULES
def set_rules():
    # add more error handling for real-time rule adjustment gaps
    config = params.get_config()
    my_rules = config.rules
    tags = config.tags
    rules = []

    if params.update_flag == True:
        my_rules.append(config.add_rule)
        tags.append(config.add_tag)
        params.update_flag = False

    for rule in my_rules:
        rules.append(
            {"value": rule, "tag": tags[my_rules.index(rule)]})
    print(("ADDED RULES USED:\n", rules))

    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    axel_rules = get_rules()
    if response.status_code != 200:
        delete_all_rules(axel_rules)
        print("Reconnecting to the stream...")
        params.recount += 1

    payload = {"add": rules}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            "Cannot add rules (HTTP {}): {}".format(
                response.status_code, response.text)
        )
    print(json.dumps(response.json()))


# UPDATE CURRENT STREAM RULES
def update_rules():
    config = params.get_config()

    if config.update_flag == True:
        delete_all_rules(get_rules())
        set_rules()
        config.update_flag = False
        print("CONFIG CHECK COMPLETE\n")


# REMOVE CURRENT STREAM RULES
def remove_rules():
    config = params.get_config()

    if config.remove_rule == "":
        return None
    else:
        config.rules.remove(params.remove_rule)
        config.tags.remove(params.remove_tag)
        params.update_flag = True
        update_rules()


def main():
    set_rules()
    rules = get_rules()
    return print("STREAM RULES SET:", rules)


# main()
