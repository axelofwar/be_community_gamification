import json
import os
import pandas as pd
import requests
from dotenv import load_dotenv
import time
from utils import stream_tools as st
from utils import postgres_tools as pg
from utils import nft_inspect_tools as nft
from utils.config import Config

if 'GITHUB_ACTION' not in os.environ:
    load_dotenv()

'''
This is app for the filtered twitter stream - contains functions for:
    - Setting up the bearer token
    - Getting the username of a tweet author by their author id
    - Getting the rules from the rules.yml file
    - Adding rules to the rules.yml file
    - Removing rules from the rules.yml file
    - Updating the rules on the Twitter API

Currently we are using the filtered stream to get tweets from the following users:
    - @y00tsNFT
    - @DeGodsNFT

Status: Working - 2023-02-23 - run the stream and store tweets matching the rules
    - store tweet ID and get info from the stream endpoint
    - get engager metrics from the stream endpoint
    - get author metrics from users endpoint by author ID from stream endpoint included user
    - create dataframes from gathered data and compare to database
    - if tweet ID is not in database, add to database
    - if tweet ID is in database, replace WHOLE database with tweets_df + updated metrics
    - create users table for with aggregated metrics from tweets table
    - if user ID is not in database, add to database
    - if user ID is in database, replace WHOLE database with users_df + updated aggregated metrics
    - create pfp table with aggregated metrics from users table taken from tweets table
    - access nft-inspect api to get pfp status and holder rank + global reach

TODO:
    - add time based functionality that resets the db every 30 days
    - do we want one app instance deploy with dynamic table and rule creation?
    - or do we want to have multiple instances for each project connecting to our same database that can modify their own rules?
'''

# Twitter API constants
# bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
# bearer_token = os.environ["TWITTER_BEARER_TOKEN"]
# Postgres constants

# print("Type of config: ", type(config))
# if config is None:
# params = Config()
params = st.params


engine = pg.start_db(params.db_name)
tweetsTable = params.metrics_table_name
usersTable = params.aggregated_table_name
pfpTable = params.pfp_table_name
newpfpTable = params.new_pfp_table_name


# check if tables exist and create if not
pg.check_metrics_table(engine, tweetsTable)
pg.check_users_table(engine, usersTable)
pg.check_pfp_table(engine, pfpTable)
pg.check_new_pfp_table(engine, newpfpTable)

# Init flags and empty frames for those used throughout the app
author = ""
df = pd.DataFrame()
export_df = pd.DataFrame()
export_include_df = pd.DataFrame()

# def get_export_df():
#     return export_include_df


def get_stream():
    config = Config.get_config(params)
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream", auth=st.bearer_oauth, stream=True,
    )

    print(response.status_code)

    if response.status_code == 429:
        print("TOO MANY REQUESTS")
        time.sleep(300)  # wait 5 minutes
        # waiting only 60 seconds doesn't seem to solve the problem
        get_stream()

    if response.status_code != 200:
        try:
            print("Reconnecting to the stream...")
            config.recount += 1
            st.set_rules(st.delete_all_rules(st.get_rules()))
        except Exception as e:
            raise Exception(
                "Cannot get stream (HTTP {}): {}: {}".format(
                    response.status_code, response.text, e
                )
            )
    for response_line in response.iter_lines():
        if response_line:
            print("\n\nGOT RESPONSE!")
            if config.update_flag == True:
                # print("UPDATING RULES")
                st.update_rules()
                config.update_flag = False

            json_response = json.loads(response_line)

            print("JSON Response: ", json_response)

            _id = json_response["data"]["id"]
            matching_rules = json_response["matching_rules"]
            tag = matching_rules[0]["tag"]
            full_text = json_response["data"]["text"]

            print("\nTEXT: ", full_text)

            # TODO: if original tweet or quoted/retweeted do we reward engager + author?
            # aggregate (x/y)*engagement to original author
            # aggregate (x/x)*engagement to quote/retweeter

            print("\nTweet_ID: ", _id)
            tweet_data = st.get_data_by_id(_id)
            # print("Tweet Data: ", tweet_data)

            totals = pd.DataFrame()
            total_members = pd.DataFrame()
            for collection in params.collections:
                print("Collection: ", collection)
                total_members = nft.get_members(engine, collection, usersTable)
                totals = pd.concat([totals, total_members])

            # see all the dudes in nft inspect datatbase wearing pfps and the metadata of the twitter image
            # for dude in totals["Name"]:
            #     if totals["Wearing PFP"][totals["Name"] == dude].values[0] == True:
            #         # print("Dude is wearing PFP: ", dude)
            #         thisUrl, thisMetadta = st.get_profile_picture_metadata(
            #             totals["Username"][totals["Name"] == dude].values[0])
            #         print(
            #             f"User {dude} is wearing NFT with metadata: {thisMetadta}")

            wearing_list, usernames, rank_list, global_reach_list, pfpUrl_list = nft.get_wearing_list(
                totals)

            non_holders = []
            memebers = pd.DataFrame(
                columns=["index", "Name", "Favorites", "Retweets", "Replies", "Impressions",
                         "Rank", "Global_Reach", "PFP_URL", "Description", "Bio_Link"]
            )

            if tweet_data["includes"]:
                print("Users: ", tweet_data["includes"]["users"])
                for user in tweet_data["includes"]["users"]:
                    # print("Author: ", user)
                    name = user["name"]
                    username = user["username"]
                    if user["name"] in wearing_list:
                        pfpurl, metadata = st.get_profile_picture_metadata(
                            username)
                        print(
                            f"User {name}, username {username} is wearing NFT with metadata: {metadata}")
                    if username in usernames and name in wearing_list:
                        rank = rank_list[usernames.index(username)]
                        global_reach = global_reach_list[usernames.index(
                            username)]
                        pfp_url = pfpUrl_list[usernames.index(username)]
                        metrics = st.get_user_metrics_by_days(
                            user["id"], params.history)
                        description, url = st.get_bio_url(username)
                        member_data = pd.DataFrame(
                            [[username, user["name"], metrics["likes"], metrics["retweets"], metrics["replies"], metrics["impressions"], rank, global_reach, pfp_url, description, url]])
                        member_data.columns = [
                            "index", "Name", "Favorites", "Retweets", "Replies", "Impressions", "Rank", "Global_Reach", "PFP_Url", "Description", "Bio_Link"]

                        pfp_table = pd.read_sql_table(newpfpTable, engine)
                        print("Calling update pfp tracked table...")
                        st.update_pfp_tracked_table(
                            engine, pfp_table, user["name"], username, metrics["likes"], metrics["retweets"], metrics[
                                "replies"], metrics["impressions"], rank, global_reach, pfpUrl, description, url
                        )
                        # print("Member Data: ", member_data)
                        memebers = pd.concat([memebers, member_data])
                    else:
                        print("Updating non holders...")
                        non_holders.append(user["username"])

                print("Holders: ", memebers["Name"].values.tolist())
                print("Non Holders: ", non_holders)

                '''
                TODO:
                - determine why frank and y00ts are not in the list of holders
                - determine if we can get pfp metadata without nft inspect
                '''


def main():
    # rules = st.get_rules()
    st.delete_all_rules(st.get_rules())
    config = Config.get_config(params)
    config.history = 30  # number of days to track back tweet metrics
    config.set_add_rule("y00ts", "y00ts")
    config.update_rules()
    config.set_add_rule("DeGods", "degods")
    config.update_rules()
    ''' Example of adding a rule for a collection -
     edit this through ssh to add more collections'''
    # config.set_add_rule("CryptoPunks", "cryptopunks")
    # config.update_rules()
    st.set_rules()
    get_stream()


if __name__ == "__main__":
    main()
