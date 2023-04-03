import json
import os
import requests
import pandas as pd
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv
if 'GITHUB_ACTION' not in os.environ:
    load_dotenv()
if "utils" not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    # print("Sys path: ", sys.path)
    from config import Config
'''
Tools for interacting with the Twitter API in a filtered stream - contains functions for:
    - Setting up the bearer token
    - Getting the username of a tweet author by their author id
    - Getting the rules from the rules.yml file
    - Adding rules to the rules.yml file
    - Removing rules from the rules.yml file
    - Updating the rules on the Twitter API
'''

# update_flag = False
# with open("utils/yamls/config.yml", "r") as file:
#     config = yaml.load(file, Loader=yaml.FullLoader)

bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
params = Config()

# config = Config.get_config()
# if config.get_config() is None:
#     config = Config()

# tweets_table = config["metrics_table_name"]
# users_table = config["aggregated_table_name"]


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
    # TODO: Determine whether we need get access modifiers or if we can
    # just use the direct attribute from the class
    # we should be able to use the attribute directly if configured properly
    config = Config.get_config(params)
    rules, my_rules = [], []

    if params.update_flag == True:
        my_rules = config.rules
        tags = config.tags
        params.update_flag = False

    for rule in my_rules:
        rules.append(
            {"value": rule, "tag": tags[my_rules.index(rule)]})
    print(("ADDED RULES USED:\n", rules))

    # Reconnect stream if not active and set rules again
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    axel_rules = get_rules()
    if response.status_code != 200:
        delete_all_rules(axel_rules)
        print("Reconnecting to the stream...")
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
    print(json.dumps(response.json()))
    config.update_flag = False


# UPDATE CURRENT STREAM RULES - read config and call set rules w/ values
def update_rules():
    config = Config.get_config(params)

    if config.update_flag == True:
        print("UPDATING RULES")
        delete_all_rules(get_rules())
        set_rules()
        config.update_flag = False


# REMOVE CURRENT STREAM RULES
def remove_rules(rules):
    config = Config.get_config(params)
    remove_it = config.remove_rule
    if remove_it == "":
        print("NO RULE IN CONFIG TO REMOVE")
        return None
    new_rules = []
    for rule in rules:
        if rule["value"] != remove_it:
            new_rules.append(rule)
    print("NEW RULES: ", new_rules)
    with open("utils/yamls/rules.yml", "w") as file:
        file.write(str(new_rules))
    # with open("utils/yamls/config.yml", "w") as file:
        config.remove_rule = ""
        # yaml.dump(config, file)
        print("REMOVE RULE RESET TO EMPTY")

    delete_all_rules(get_rules())
    set_rules(new_rules)
    config.update_flag = False
    return config.update_flag


# USE TWEETS ENDPOINT TO GET TWEEET DATA BY TWEET ID
def get_data_by_id(tweet_id):
    response = requests.get(
        f"https://api.twitter.com/2/tweets/{tweet_id}?expansions=author_id,entities.mentions.username,geo.place_id,referenced_tweets.id&media.fields=url&poll.fields=options&tweet.fields=public_metrics",
        auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get tweet data (HTTP {}): {}".format(
                response.status_code, response.text)
        )
    return response.json()


# GET ENGAGEMENT METRICS FOR TWEET BY TWEET ID
def get_tweet_metrics(tweet_id):
    response = requests.get(
        f"https://api.twitter.com/1.1/statuses/show.json?id={tweet_id}",
        auth=bearer_oauth
    )

    if response.status_code != 200:
        raise Exception(
            "Cannot get tweet data (HTTP {}): {}".format(
                response.status_code, response.text)
        )
    return response.json()

# CALL USERS ENDPOINT FOR USERNAME OF TWEETER BY TWEET AUTHOR ID


def get_username_by_author_id(author_id):
    response = requests.get(
        f"https://api.twitter.com/2/users/{author_id}",
        auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get user data (HTTP {}): {}".format(
                response.status_code, response.text)
        )
    return response.json()


def get_user_metrics_by_days(user_id, days):

    aggregated_likes, aggregated_retweets, aggregated_replies, aggregated_impressions = 0, 0, 0, 0

    end_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    start_date = (datetime.utcnow() - timedelta(days=days)
                  ).strftime('%Y-%m-%dT%H:%M:%SZ')

    url = f"https://api.twitter.com/2/users/{user_id}/tweets?max_results=100&tweet.fields=public_metrics&start_time={start_date}&end_time={end_date}"

    try:
        response = requests.get(
            url, headers={"Authorization": f"Bearer {bearer_token}"})

        if response.status_code != 200:
            raise Exception(
                f"Failed to get user metrics (HTTP {response.status_code}): {response.text}")
    except Exception as e:
        print(e)
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

    # # Aggregate the metrics for all tweets
    # metrics = {"likes": 0, "retweets": 0, "replies": 0, "impressions": 0}
    # for tweet in data["data"]:
    #     for key in metrics.keys():
    #         metrics[key] += tweet["public_metrics"][key]

    return data


def get_bio_url(author):
    response = requests.get(
        url=f"https://api.twitter.com/2/users/by/username/{author}?user.fields=description,url",
        # f"https://api.twitter.com/2/users/{author_id}?user.fields=description,url",
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


def get_profile_picture_metadata(username):
    response = requests.get(
        url=f"https://api.twitter.com/2/users/by/username/{username}?user.fields=profile_image_url",
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


'''
TODO: Confirm that the update_aggregated_metrics function is
working as intended. It should only update rows that have changed
and not the entire table. We still need to confirm if the += logic
being using to aggregate the values is correct. It should be

'''


def update_aggregated_metrics(engine, author_username, users_df, tweets_df):
    config = Config.get_config(params)
    users_table = config.get_aggregated_table_name()
    # Get the row in `users_df` where the index matches the author_username
    user_row = users_df[users_df["index"] == author_username]
    current_likes = user_row["Favorites"].values[0]
    current_retweets = user_row["Retweets"].values[0]
    current_replies = user_row["Replies"].values[0]
    current_impressions = user_row["Impressions"].values[0]

    # Iterate through the rows in `tweets_df` where the index matches the author_username,
    # and update the aggregated values with the changed values
    for _, row in tweets_df[tweets_df["index"] == author_username].iterrows():
        current_likes += row["Favorites"]
        current_retweets += row["Retweets"]
        current_replies += row["Replies"]
        current_impressions += row["Impressions"]

    # Check if `aggregated_impressions` is still 0, and if so, update it with the value from `users_df`
    if current_impressions == 0:
        current_impressions = user_row["Impressions"].values[0]

    # Only update the aggregated values in `users_df` if they have changed
    if (current_likes != user_row["Favorites"].values[0] or
        current_retweets != user_row["Retweets"].values[0] or
        current_replies != user_row["Replies"].values[0] or
            current_impressions != user_row["Impressions"].values[0]):

        users_df.loc[users_df["index"] == author_username,
                     "Favorites"] = current_likes
        users_df.loc[users_df["index"] == author_username,
                     "Retweets"] = current_retweets
        users_df.loc[users_df["index"] == author_username,
                     "Replies"] = current_replies
        users_df.loc[users_df["index"] == author_username,
                     "Impressions"] = current_impressions

        # Write the updated `users_df` to the database
        users_df.to_sql(users_table, engine,
                        if_exists="replace", index=False)
        print(
            f"Aggregated values for {author_username} in Users table updated")
        # print("Agg DF Users Table: ", users_df)
    else:
        print(f"No changes to aggregated values for {author_username}")


'''
TODO: Confirm that the update_tweets_table function is working properly
this method should only update the values in the table if they have increased
If it isn't then use then revert to chatGPT-helpbot's method of updating the table
'''


def update_tweets_table(engine, id, tweets_df, included_likes, included_retweets, included_replies, included_impressions):
    config = Config.get_config(params)
    tweets_table = config.get_metrics_table_name()
    print(
        f"Tweet #{id} already exists in Metrics table +\
        \nUpdating Metrics table...")
    # get the row that needs to be updated
    row = tweets_df.loc[tweets_df["Tweet_ID"] == id]
    row = row.values[0]

    # drop unnecessary columns if present
    if len(row) > 6:
        row = row[1:]
        if "level_0" in tweets_df.columns:
            print("DAMNIT")
            tweets_df.dropna(inplace=True)
            tweets_df.drop(columns=["level_0"], axis=1, inplace=True)

    # get current metrics
    favorites = row[2]
    retweets = row[3]
    replies = row[4]
    impressions = row[5]

    # update the values in the existing table if they have increased
    updated_metrics = {}
    if int(included_likes) > int(favorites):
        print(f"Metrics Likes updated to {included_likes}")
        tweets_df.loc[tweets_df["Tweet_ID"] ==
                      id, ["Favorites"]] = included_likes
        updated_metrics["Favorites"] = included_likes

    if int(included_retweets) > int(retweets):
        print(f"Metrics Retweets updated to {included_retweets}")
        tweets_df.loc[tweets_df["Tweet_ID"] ==
                      id, ["Retweets"]] = included_retweets
        updated_metrics["Retweets"] = included_retweets

    if int(included_replies) > int(replies):
        print(f"Metrics Replies updated to {included_replies}")
        tweets_df.loc[tweets_df["Tweet_ID"] ==
                      id, ["Replies"]] = included_replies
        updated_metrics["Replies"] = included_replies

    if int(included_impressions) > int(impressions):
        print(f"Metrics Impressions updated to {included_impressions}")
        tweets_df.loc[tweets_df["Tweet_ID"] == id,
                      ["Impressions"]] = included_impressions
        updated_metrics["Impressions"] = included_impressions

    # update only the rows that have changed - sql query
    if updated_metrics:
        print(f"Updating Tweets Table with updated metrics: {updated_metrics}")
        engine.execute(f"""
            UPDATE {tweets_table}
            SET {','.join([f'"{k}" = {v}' for k,v in updated_metrics.items()])}
            WHERE "Tweet_ID" = '{id}'
        """)  # extra ' after f is needed to uppercase the column names

    # drop unnecessary columns if present
    if "level_0" in tweets_df.columns:
        print("DAMNIT level_0 LOL")
        tweets_df.drop(columns=["level_0"], inplace=True)

    print("Metrics table updated")


'''
TODO: Confirm that the update_pfp_tracked_table function is working properly
this method should only update the values in the table if they have increased
If it isn't then use then revert to chatGPT-helpbot's method of updating the table
'''


def update_pfp_tracked_table(engine, pfp_table, name, username, agg_likes, agg_retweets, agg_replies, agg_impressions, rank, global_reach, pfpUrl, desc, url):
    config = Config.get_config(params)
    # pfp_table_name = config.get_pfp_table_name() # temp commented out
    print("Updating PFP Tracked Table...")
    # check if the user is already in the table
    pfp_table_name = config.new_pfp_table_name  # temp added
    pfp_table = pd.read_sql_table(pfp_table_name, engine)

    if pfp_table.empty:
        print("PFP Tracked Table is empty")
        pfp_table = pd.DataFrame({
            "index": [username],
            "Name": [name],
            "Favorites": [agg_likes],
            "Retweets": [agg_retweets],
            "Replies": [agg_replies],
            "Impressions": [agg_impressions],
            "Rank": [rank],
            "Global_Reach": [global_reach],
            "PFP_Url": [pfpUrl],
            "Description": [desc],
            "Bio_Link": [url]
        })
        print("PFP Tracked Table Created: ", pfp_table)
        pfp_table.to_sql(pfp_table_name, engine,
                         if_exists="replace", index=False)
        print(f"User {name} added to PFP Tracked Table")
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
            if user_row["Rank"] is None or rank > user_row["Rank"]:
                updates["Rank"] = rank if user_row["Rank"] is None else max(
                    rank, user_row["Rank"])
            if user_row["Global_Reach"] is None or global_reach > user_row["Global_Reach"]:
                updates["Global_Reach"] = global_reach if user_row["Global_Reach"] is None else max(
                    global_reach, user_row["Global_Reach"])
            # hard set these each time as they are harder to compare than values
            if user_row["PFP_Url"] is None or pfpUrl != user_row["PFP_Url"]:
                updates["PFP_Url"] = pfpUrl
            if user_row["Description"] is None or desc != user_row["Description"]:
                updates["Description"] = desc
            if user_row["Bio_Link"] is None or url != user_row["Bio_Link"]:
                updates["Bio_Link"] = url

            if updates:
                pfp_table.loc[user_index, updates.keys()] = updates.values()
                print(f"PFP Tracked values updated for user {name}: {updates}")
        else:
            new_row = pd.DataFrame({
                "index": [username],
                "Name": [name],
                "Favorites": [agg_likes],
                "Retweets": [agg_retweets],
                "Replies": [agg_replies],
                "Impressions": [agg_impressions],
                "Rank": [rank],
                "Global_Reach": [global_reach],
                "PFP_Url": [pfpUrl],
                "Description": [desc],
                "Bio_Link": [url]
            })
            pfp_table = pfp_table.append(new_row, ignore_index=True)
            pfp_table.to_sql(pfp_table_name, engine,
                             if_exists="replace", index=False)
            print(f"User {username} added to {pfp_table_name}")

    return pfp_table


def create_dataFrame(id, author_username, author_name, likes, retweets, replies, impressions):
    authors_index = [author_username]

    df0 = pd.DataFrame(
        index=authors_index, data=author_name, columns=["Author"])
    df1 = pd.DataFrame(
        index=authors_index, data=int(likes), columns=["Favorites"])
    df2 = pd.DataFrame(
        index=authors_index, data=int(retweets), columns=["Retweets"])
    df3 = pd.DataFrame(
        index=authors_index, data=int(replies), columns=["Replies"])
    df4 = pd.DataFrame(
        index=authors_index, data=int(impressions), columns=["Impressions"])
    df5 = pd.DataFrame(
        index=authors_index, data=id, columns=["Tweet_ID"])
    df = pd.concat([df0, df1, df2, df3, df4, df5], axis=1)

    return df


def create_metric_dataFrame(id, author_username, author_name, likes, retweets, replies, impressions, tag):
    authors_index = [author_username]

    df0 = pd.DataFrame(
        index=authors_index, data=author_name, columns=["Author"])
    df1 = pd.DataFrame(
        index=authors_index, data=int(likes), columns=["Favorites"])
    df2 = pd.DataFrame(
        index=authors_index, data=int(retweets), columns=["Retweets"])
    df3 = pd.DataFrame(
        index=authors_index, data=int(replies), columns=["Replies"])
    df4 = pd.DataFrame(
        index=authors_index, data=int(impressions), columns=["Impressions"])
    df5 = pd.DataFrame(
        index=authors_index, data=id, columns=["Tweet_ID"])
    df6 = pd.DataFrame(
        index=authors_index, data=tag, columns=["Tag"])
    df = pd.concat([df0, df1, df2, df3, df4, df5, df6], axis=1)
    return df


# def main():
#     user = "axelofwar"
#     url, metadata = get_profile_picture_metadata(user)
#     print("URL: ", url)
#     print("Metadata: ", metadata)
#     metrics = get_user_metrics_by_days("1434237661728882694", 7)
#     print("Metrics: ", metrics)

#     '''
#     Author ID: 1434237661728882694, Author Name: PixelRainbowNFT (aka 5h4gg0) 💀🍟, Author Username: PixelRainbowNFT
#     '''
#     desc, urls = get_bio_url("Epicurus33")
#     print("Description: ", desc)
#     print("URLs: ", urls)
# #     config = Config.get_config(params)
# #     # config = Config()
# #     # config = Config.get_config()
# #     # Config.set_add_rule("myRule", "accounts")
# #     # Config.update_rules()
# #     # Config.set_remove_rule("myRule")
# #     # Config.update_rules()
# #     # update_rules()
# #     config.get_config()
# #     config.set_add_rule("myRule", "accounts")
# #     config.update_rules()
# #     config.set_remove_rule("myRule")
# #     config.update_rules()


# main()
