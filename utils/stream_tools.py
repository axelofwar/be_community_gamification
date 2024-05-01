import json
import os
import requests
import pandas as pd
import sys
from datetime import datetime, timedelta
import logging
import requests
from typing import List, Dict, Tuple
from sqlalchemy.engine import Engine

from dotenv import load_dotenv
if 'GITHUB_ACTION' not in os.environ:
    load_dotenv()
if "utils" not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    # print("Sys path: ", sys.path)
    from config import Config
else:
    from config import Config
'''
Tools for interacting with the Twitter API in a filtered stream - contains functions for:
    - Setting up the bearer token
    - Getting the username of a tweet author by their author id
    - Getting the rules from the rules.yml file
    - Adding rules to the rules.yml file
    - Removing rules from the rules.yml file
    - Updating the rules on the Twitter API

TODO: Determine whether we need get access modifiers or use the direct attribute from the class. Ex line 133: `config = Config.get_config(params)`
'''

bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
params = Config()

# SET BEARER TOKEN AUTH
def bearer_oauth(r: requests.PreparedRequest) -> requests.PreparedRequest:
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FilteredStreamPython"
    return r


# GET RULES OF CURRENT STREAM
def get_rules() -> Dict:
    """
    Get the current twitter stream rules

    :return json_response: Dict of rules
    """
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(
                response.status_code, response.text)
        )
    logging.info(json.dumps(response.json()))
    return response.json()


# DELETE CURRENT SET STREAM SET RULES
def delete_all_rules(rules: List) -> None:
    """
    Send request to the endpoint for deleting current stream rules
    """
    if rules is None or "data" not in rules:
        return None

    ids = list(map(lambda rule: int(rule["id"]), rules["data"]))
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
    logging.info(json.dumps(response.json()))


# SET CURRENT STREAM RULES
def set_rules() -> None:
    """
    Set the stream rules for the current Twitter API stream
    """
    config = Config.get_config(params)
    rules, my_rules = [], []

    if params.update_flag == True:
        my_rules = config.rules
        tags = config.tags
        params.update_flag = False

    for rule in my_rules:
        rules.append(
            {"value": rule, "tag": tags[my_rules.index(rule)]})
    logging.info((f"ADDED RULES USED:\n {rules}"))

    # Reconnect stream if not active and set rules again
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    axel_rules = get_rules()
    if response.status_code != 200:
        delete_all_rules(axel_rules)
        logging.info("Reconnecting to the stream...")
        config.recount += 1

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
    logging.info(json.dumps(response.json()))
    config.update_flag = False


def update_rules() -> None:
    """
    Set new rules to the Twitter API stream from config
    """
    config = Config.get_config(params)

    if config.update_flag == True:
        print("UPDATING RULES")
        delete_all_rules(get_rules())
        set_rules()
        config.update_flag = False


# REMOVE CURRENT STREAM RULES
def remove_rules(rules: List) -> bool:
    """
    Remove the current rules on the Twitter API stream
    """
    config = Config.get_config(params)
    remove_it = config.remove_rule
    if remove_it == "":
        logging.warning("NO RULE IN CONFIG TO REMOVE")
        config.update_flag = False
        return config.update_flag
    new_rules = []
    for rule in rules:
        if rule["value"] != remove_it:
            new_rules.append(rule)
    logging.debug("NEW RULES: {new_rules}")
    with open("utils/yamls/rules.yml", "w") as file:
        file.write(str(new_rules))
        config.remove_rule = ""
        logging.info("REMOVE RULE RESET TO EMPTY")

    delete_all_rules(get_rules())
    # set_rules(new_rules) # shouldn't need new_rules passed
    set_rules()
    config.update_flag = False
    return config.update_flag


# USE TWEETS ENDPOINT TO GET TWEEET DATA BY TWEET ID
def get_data_by_id(tweet_id: str) -> Dict:
    """
    Return the data for the tweet given its tweet ID - including user and metrics info

    :param tweet_id: (Self-explanatory)
    """
    response = requests.get(
        f"https://api.twitter.com/2/tweets/{str(tweet_id)}?expansions=author_id,entities.mentions.username,geo.place_id,referenced_tweets.id&media.fields=url&poll.fields=options&tweet.fields=public_metrics",
        auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get tweet data (HTTP {}): {}".format(
                response.status_code, response.text)
        )
    return response.json()


# GET ENGAGEMENT METRICS FOR TWEET BY TWEET ID
def get_tweet_metrics(tweet_id: str) -> Dict:
    """
    Return the current metrics for the tweet by tweet ID

    :param tweet_id: (Self-explanatory)
    return: json response 
    """
    response = requests.get(
        f"https://api.twitter.com/1.1/statuses/show.json?id={str(tweet_id)}",
        auth=bearer_oauth
    )

    if response.status_code != 200:
        raise Exception(
            "Cannot get tweet data (HTTP {}): {}".format(
                response.status_code, response.text)
        )
    return response.json()

# CALL USERS ENDPOINT FOR USERNAME OF TWEETER BY TWEET AUTHOR ID


def get_username_by_author_id(author_id: str) -> Dict:
    """
    Get twitter username from author ID

    :param author_id: (Self-explanatory)
    return: json response 
    """
    response = requests.get(
        f"https://api.twitter.com/2/users/{str(author_id)}",
        auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get user data (HTTP {}): {}".format(
                response.status_code, response.text)
        )
    return response.json()


def get_twitter_user_info(username: str) -> Dict:
    """
    Get twitter user info from username

    :param username: (Self-explanatory)
    return: json response 
    """
    # Twitter API endpoint for user lookup
    url = f'https://api.twitter.com/2/users/by/username/{username}'

    try:
        response = requests.get(
            url, headers={"Authorization": f"Bearer {bearer_token}"})

        if response.status_code != 200:
            raise Exception(
                f"Failed to get user metrics (HTTP {response.status_code}): {response.text}")
    except Exception as e:
        logging.error(e)
    return response.json()["data"]


def get_user_metrics_start_end(user_id: str, start_date: str, end_date: str) -> Dict:

    aggregated_likes, aggregated_retweets, aggregated_replies, aggregated_impressions = 0, 0, 0, 0

    url = f"https://api.twitter.com/2/users/{str(user_id)}/tweets?max_results=100&tweet.fields=public_metrics&start_time={str(start_date)}&end_time={str(end_date)}"

    try:
        response = requests.get(
            url, headers={"Authorization": f"Bearer {bearer_token}"})

        if response.status_code != 200:
            raise Exception(
                f"Failed to get user metrics (HTTP {response.status_code}): {response.text}")
    except Exception as e:
        logging.error(e)

    # Parse the response JSON
    data = response.json()
    for tweet in data["data"]:
        aggregated_likes += tweet["public_metrics"]["like_count"]
        aggregated_retweets += tweet["public_metrics"]["retweet_count"]
        aggregated_replies += tweet["public_metrics"]["reply_count"]
        aggregated_impressions += tweet["public_metrics"]["impression_count"]

        data = {
            "likes": aggregated_likes,
            "retweets": aggregated_retweets,
            "replies": aggregated_replies,
            "impressions": aggregated_impressions
        }

    return data


def get_user_metrics_by_days(user_id, days) -> Dict:
    """
    Get user metrics given # days requested

    :param user_id: (self-explanatory)
    :param days: (self-explanatory)

    return: json response
    """

    aggregated_likes, aggregated_retweets, aggregated_replies, aggregated_impressions = 0, 0, 0, 0

    end_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    start_date = (datetime.utcnow() - timedelta(days=days)
                  ).strftime('%Y-%m-%dT%H:%M:%SZ')

    # current_time = datetime.utcnow()

    # if 'start_date' not in locals() or (current_time - datetime.fromisoformat(start_date)) >= timedelta(days=params.history):
    #     start_date = (current_time - timedelta(days=params.history)
    #                   ).strftime('%Y-%m-%dT%H:%M:%SZ')
    #     end_date = (current_time + timedelta(days=1)
    #                 ).strftime('%Y-%m-%dT%H:%M:%SZ')
    # else:
    #     end_date = (datetime.fromisoformat(end_date) +
    #                 timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')

    logging.debug(f"START DATE: {start_date}")
    logging.debug(f"END DATE: {end_date}")

    url = f"https://api.twitter.com/2/users/{str(user_id)}/tweets?max_results=100&tweet.fields=public_metrics&start_time={str(start_date)}&end_time={str(end_date)}"

    try:
        response = requests.get(
            url, headers={"Authorization": f"Bearer {bearer_token}"})

        if response.status_code != 200:
            raise Exception(
                f"Failed to get user metrics (HTTP {response.status_code}): {response.text}")
    except Exception as e:
        logging.error(e)
    # Parse the response JSON
    data = response.json()
    for tweet in data["data"]:
        aggregated_likes += tweet["public_metrics"]["like_count"]
        aggregated_retweets += tweet["public_metrics"]["retweet_count"]
        aggregated_replies += tweet["public_metrics"]["reply_count"]
        aggregated_impressions += tweet["public_metrics"]["impression_count"]

        data = {
            "likes": aggregated_likes,
            "retweets": aggregated_retweets,
            "replies": aggregated_replies,
            "impressions": aggregated_impressions
        }

    # TODO: determine best method of aggregating across all tweets
    # Aggregate the metrics for all tweets
    # metrics = {"likes": 0, "retweets": 0, "replies": 0, "impressions": 0}
    # for tweet in data["data"]:
    #     for key in metrics.keys():
    #         metrics[key] += tweet["public_metrics"][key]

    return data


def get_bio_url(author: str) -> Tuple[str, str]:
    """
    Get bio and url in bio of user

    :param author: (self-explanatory)

    return: description/bio and url
    """
    response = requests.get(
        url=f"https://api.twitter.com/2/users/by/username/{str(author)}?user.fields=description,url",
        auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get user data (HTTP {}): {}".format(
                response.status_code, response.text)
        )
    data = response.json()["data"]
    try:
        desc = data["description"]
    except KeyError:
        desc = "None"
    try:
        urls = data["url"]
    except KeyError:
        urls = "None"
    return desc, urls


def get_profile_picture_metadata(username: str) -> Tuple[str, Dict[str, str]]:
    """
    Get the metadata of the users profile picture

    :param username: (self-explanatory)
    
    :return: image url and response headers
    """
    response = requests.get(
        url=f"https://api.twitter.com/2/users/by/username/{str(username)}?user.fields=profile_image_url",
        auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get user data (HTTP {}): {}".format(
                response.status_code, response.text)
        )
    data = response.json()["data"]
    try:
        profile_image_url = data["profile_image_url"]
    except KeyError:
        profile_image_url = "None"

    response = requests.head(profile_image_url)
    if response.status_code != 200:
        raise Exception(
            "Cannot get user data (HTTP {}): {}".format(
                response.status_code, response.text)
        )
    return profile_image_url, response.headers


def update_pfp_tracked_table(engine: Engine, 
                             name: str, 
                             username: str, 
                             agg_likes: int, 
                             agg_retweets: int, 
                             agg_replies: int, 
                             agg_impressions: int, 
                             # rank, 
                             # global_reach, 
                             pfp_url: str, 
                             desc: str, 
                             url: str) -> pd.DataFrame:
    '''Function for reading the pfp_table and updating the desired user's metrics. 
    Depreciated use of nft-inspect API for rank and global reach.

    :param engine: Instance of connection to PostgreSQL database
    :param name: the name of the user to update
    :param username: the correspdoning username of the user to update
    :param agg_likes: aggregated likes to update the user with
    :param agg_retweets: aggregated retweets to update the user with
    :param agg_replies: aggregated replies to update the user with
    :param agg_impressions: the aggregated impressions to update
    :param pfp_url: the url of where twitter stores the users pfp image
    :param desc: the description associated with the users Twitter account
    :param url: the url or link in the user's Twitter bio.

    TODO: Confirm that the update_pfp_tracked_table function is working properly
    this method should only update the values in the table if they have increased
    If it isn't then use then revert to chatGPT-helpbot's method of updating the table
    '''
    config = Config.get_config(params)
    # pfp_table_name = config.get_pfp_table_name() # temp commented out
    logging.info("Updating PFP Tracked Table...")
    # check if the user is already in the table
    pfp_table_name = config.new_pfp_table_name  # temp added
    pfp_table = pd.read_sql_table(pfp_table_name, engine)

    if pfp_table.empty:
        logging.warning("PFP Tracked Table is empty")
        pfp_table = pd.DataFrame({
            "index": [username],
            "Name": [name],
            "Favorites": [agg_likes],
            "Retweets": [agg_retweets],
            "Replies": [agg_replies],
            "Impressions": [agg_impressions],
            # "Rank": [rank],
            # "Global_Reach": [global_reach],
            "PFP_Url": [pfp_url],
            "Description": [desc],
            "Bio_Link": [url]
        })
        logging.info(f"PFP Tracked Table Created: {pfp_table}")
        pfp_table.to_sql(pfp_table_name, engine,
                         if_exists="replace", index=False)
        logging.info(f"User {name} added to PFP Tracked Table")
    else:
        user_exists = pfp_table["index"] == username
        if user_exists.any():
            user_index = user_exists.idxmax()
            user_row = pfp_table.loc[user_index]
            updates = {}

            '''
            check if the value is None, and if it is then assign
            the value of the table. If it is None, compare the max of
            the current value and the new value
            '''

            if user_row["Favorites"] is None or agg_likes > user_row["Favorites"]:
                updates["Favorites"] = agg_likes if user_row["Favorites"] is None else max(
                    agg_likes, user_row["Favorites"])
            if user_row["Retweets"] is None or agg_retweets > user_row["Retweets"]:
                updates["Retweets"] = agg_retweets if user_row["Retweets"] is None else max(
                    agg_retweets, user_row["Retweets"])
            if user_row["Replies"] is None or agg_replies > user_row["Replies"]:
                updates["Replies"] = agg_replies if user_row["Replies"] is None else max(
                    agg_replies, user_row["Replies"])
            if user_row["Impressions"] is None or agg_impressions > user_row["Impressions"]:
                updates["Impressions"] = agg_impressions if user_row["Impressions"] is None else max(
                    agg_impressions, user_row["Impressions"])
            # if user_row["Rank"] is None or rank > user_row["Rank"]:
            #     updates["Rank"] = rank if user_row["Rank"] is None else max(
            #         rank, user_row["Rank"])
            # if user_row["Global_Reach"] is None or global_reach > user_row["Global_Reach"]:
            #     updates["Global_Reach"] = global_reach if user_row["Global_Reach"] is None else max(
            #         global_reach, user_row["Global_Reach"])
            # hard set these each time as they are harder to compare than values
            if user_row["PFP_Url"] is None or pfp_url != user_row["PFP_Url"]:
                updates["PFP_Url"] = pfp_url
            if user_row["Description"] is None or desc != user_row["Description"]:
                updates["Description"] = desc
            if user_row["Bio_Link"] is None or url != user_row["Bio_Link"]:
                updates["Bio_Link"] = url

            if updates:
                pfp_table.loc[user_index, updates.keys()] = updates.values()
                logging.info(f"PFP Tracked values updated for user {name}: {updates}")
        else:
            new_row = pd.DataFrame({
                "index": [username],
                "Name": [name],
                "Favorites": [agg_likes],
                "Retweets": [agg_retweets],
                "Replies": [agg_replies],
                "Impressions": [agg_impressions],
                # "Rank": [rank],
                # "Global_Reach": [global_reach],
                "PFP_Url": [pfp_url],
                "Description": [desc],
                "Bio_Link": [url]
            })
            pfp_table = pfp_table.append(new_row, ignore_index=True)
            pfp_table.to_sql(pfp_table_name, engine,
                             if_exists="replace", index=False)
            logging.info(f"User {username} added to {pfp_table_name}")

    return pfp_table