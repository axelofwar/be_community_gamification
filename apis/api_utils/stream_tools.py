import json
import os
import requests
import yaml
import pandas as pd
from dotenv import load_dotenv
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

update_flag = False
with open("../utils/yamls/config.yml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
# bearer_token = os.environ["TWITTER_BEARER_TOKEN"]
tweetsTable = config["metrics_table_name"]
usersTable = config["aggregated_table_name"]


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
def set_rules(delete, update_flag, rule, tag):
    # add more error handling for real-time rule adjustment gaps
    with open("../utils/yamls/rules.yml", "r") as file:
        axel_rules = yaml.load(file, Loader=yaml.FullLoader)
    with open("../utils/yamls/config.yml", "r") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    print("RULES SAVED TO rules.yml")
    print("UPDATE VALUE IN SET: ", update_flag)
    if update_flag:
        axel_rules = axel_rules + \
            [{"value": rule, "tag": tag}, ]
        with open("../utils/yamls/rules.yml", "w") as file:
            file.write(str(axel_rules))

        print("RULE VALUE UPDATED:\n", update_flag)
        print(("ADDED RULES USED:\n", axel_rules))

    # Reconnect stream if not active and set rules again
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    rules = get_rules()
    if response.status_code != 200:
        delete_all_rules(rules)
        print("Reconnecting to the stream...")
        with open("utils/yamls/config.yml", "w") as file:
            config["RECONNECT_COUNT"] += 1
            yaml.dump(config, file)

    payload = {"add": axel_rules}
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
    with open("../utils/yamls/config.yml", "r") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    if "ADD_RULE" in config:
        rule = config["ADD_RULE"]
        tag = config["ADD_TAG"]
        update_flag = True
        # print(f"UPDATED TO {update_flag}")
    else:
        print("No rule to add")

    if rule == "" or rule == None:
        update_flag = False
        # print(f"UPDATED TO {update_flag}")
    else:
        print("SETTING NEW RULES")
        delete = delete_all_rules(get_rules())
        if "'" or '"' in rule:
            # rule = rule.replace('"', "")
            rule = rule.replace(" ", "")
            rule = rule.replace(",", "")
            rule = rule.replace("'", "")
        if "'" or '"' in tag:
            tag = tag.replace("'", "")
            # tag = tag.replace('"', "")
            tag = tag.replace(" ", "")
            tag = tag.replace(",", "")
        print("RULE TO ADD: ", rule)
        print("TAG TO ADD: ", tag)

        set_rules(delete, update_flag, rule, tag)
        print("RULES UPDATED")
        update_flag = False
    with open("../utils/yamls/config.yml", "w") as file:
        config["ADD_RULE"] = ""
        config["ADD_TAG"] = ""
        yaml.dump(config, file)
        print("CONFIG CHECK COMPLETE\n")


# REMOVE CURRENT STREAM RULES
def remove_rules(rules):
    remove_it = config["REMOVE_RULE"]
    if remove_it == "":
        return None
    new_rules = []
    for rule in rules:
        if "'" or '"' in rule:
            rule["value"] = rule["value"].replace("'", "")
            rule["value"] = rule["value"].replace('"', "")

        if rule["value"] != remove_it:
            new_rules.append(rule)
    print("NEW RULES: ", new_rules)
    with open("../utils/yamls/rules.yml", "w") as file:
        file.write(str(new_rules))
    with open("../utils/yamls/config.yml", "w") as file:
        config["REMOVE_RULE"] = ""
        yaml.dump(config, file)
        print("REMOVE RULE RESET TO EMPTY")

    delete_all_rules(get_rules())
    set_rules(new_rules, update_flag, rule)
    remove_flag = True
    return remove_flag


def main():
    # delete_all_rules(get_rules())
    with open("../utils/yamls/rules.yml", "r") as file:
        rules = yaml.load(file, Loader=yaml.FullLoader)
    # set_rules(rules, update_flag, "this", "test")
    rules = get_rules()
    return print("STREAM RULES SET:", rules)


main()
