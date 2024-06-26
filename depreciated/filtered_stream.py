import json
import os
import pandas as pd
import requests
from dotenv import load_dotenv
import time
import stream_tools as st
import postgres_tools as pg
import nft_inspect_tools as nft
from config import Config

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


# check if tables exist and create if not
pg.check_metrics_table(engine, tweetsTable)
pg.check_users_table(engine, usersTable)
pg.check_pfp_table(engine, pfpTable)

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

            _id = json_response["data"]["id"]
            matching_rules = json_response["matching_rules"]
            tag = matching_rules[0]["tag"]
            full_text = json_response["data"]["text"]
            print("\nMATCHING RULES: ", matching_rules)
            '''
            We can use this matching rules object in the future to 
            determine which project's table we should add the data to
            '''
            print("\nTEXT: ", full_text)

            # TODO: if original tweet or quoted/retweeted do we reward engager + author?
            # aggregate (x/y)*engagement to original author
            # aggregate (x/x)*engagement to quote/retweeter

            print("\nTweet_ID: ", _id)
            tweet_data = st.get_data_by_id(_id)

            # improve wait/sleep to make sure rules GET call has returned json respones
            # once this is done, remove the nested if and try checks
            try:
                if tweet_data["data"]["author_id"]:
                    if "author_id" in tweet_data["data"]:
                        author_id = tweet_data["data"]["author_id"]
                        author = st.get_username_by_author_id(
                            tweet_data["data"]["author_id"])
                        author_username = author["data"]["username"]
                        author_name = author["data"]["name"]
                        print(
                            f"\nAuthor ID: {author_id}, Author Name: {author_name}, \
                                Author Username: {author_username}")
                    else:
                        print("Author ID not found")

                if "referenced_tweets" in tweet_data["data"]:
                    if tweet_data["data"]["referenced_tweets"]:
                        referenced = tweet_data["data"]["referenced_tweets"]
                    # print("\nReferenced Tweets: ", referenced)

                if "tweets" in tweet_data["includes"]:
                    if tweet_data["includes"]["tweets"]:
                        included_tweets = tweet_data["includes"]["tweets"]
                        included_users = tweet_data["includes"]["users"]
                    else:
                        included_tweets = None
                        included_users = None

            except KeyError as ke:
                print("KeyError occured: ", ke)
                # config.increment_recount()
                config.recount += 1
                print("Restarting stream...")
                get_stream()

            _id = tweet_data["data"]["id"]
            # print("\nTweet_ID by tweet_data: ", _id)
            engagement_metrics = st.get_tweet_metrics(_id)
            tweet_favorite_count = int(engagement_metrics["favorite_count"])
            tweet_retweet_count = int(engagement_metrics["retweet_count"])
            # print(
            #     f"\nTweet Favorites: {tweet_favorite_count}, Tweet Retweets: {tweet_retweet_count}")

            # TODO: create a new table for each new rule(project?) allows by communtiy tracking
            # do we want to deploy a new instance of the app for each project?
            # or do we want to have a single instance of the app that can track multiple projects?

            # TODO: index by tweetID on metrics table instead of author username in order to prevent duplicate rows
            authors_index = [author_username]
            df0 = pd.DataFrame(
                index=authors_index, data=author_name, columns=["Author"])
            df1 = pd.DataFrame(index=authors_index, data=int(
                tweet_favorite_count), columns=["Favorites"])
            df2 = pd.DataFrame(index=authors_index, data=int(
                tweet_retweet_count), columns=["Retweets"])
            df3 = pd.DataFrame(index=authors_index,
                               data=id, columns=["Tweet_ID"])
            df = pd.concat([df0, df1, df2, df3], axis=1)

            # export_df = df
            # print("\nExport_df:", export_df)

            if tweet_data["includes"] and "tweets" in tweet_data["includes"]:
                # loop to go through all referenced/included tweets
                for iter in range(len(included_tweets)):
                    included = included_tweets[iter]
                    included_id = included["id"]
                    included_author_id = included["author_id"]
                    included_pub_metrics = included["public_metrics"]

                    included_likes = included_pub_metrics["like_count"]
                    included_replies = int(
                        included_pub_metrics["reply_count"])
                    included_retweets = included_pub_metrics["retweet_count"]
                    # included_quote_count = included_pub_metrics["quote_count"]
                    included_impressions = int(
                        included_pub_metrics["impression_count"])

                    # print("\nIncluded Tweet_ID: ", included_id)
                    # print("\nIncluded/Parent Tweet Author ID: ",
                    #       included_author_id)

                    if included_author_id == author_id:
                        included_author_username = author_username
                        included_author_name = author_name
                    else:
                        try:
                            included_name = st.get_username_by_author_id(
                                included_author_id)
                            included_author_username = included_name["data"]["username"]
                            included_author_name = included_name["data"]["name"]

                            df = st.create_metric_dataFrame(included_id, included_author_username, author_name, included_likes,
                                                            included_retweets, included_replies, included_impressions, tag)
                        except Exception as err:
                            print("ERROR ON GET USERNAME BY AUTHOR ID ", err)

                    # print("\nAUTHOR OF INCLUDED/PARENT TWEET DIFFERENT FROM AUTHOR")
                    # print("\nIncluded/Parent Likes: ", included_likes)
                    # print("\nIncluded/Parent Replies: ", included_replies)
                    # print("\nIncluded/Parent Retweets: ", included_retweets)
                    # print("\nIncluded/Parent Quotes: ", included_quote_count)
                    # print("\nIncluded/Parent Impressions: ",
                    #       included_impressions)
                    export_include_df = df

                for iter in range(len(included_users)):
                    engager_user = included_users[iter]
                    engager_id = engager_user["id"]
                    # uncomment this and parse each author id if we want to give points to each mentioned user
                    # print("\nMentioned ID #: ", iter, " ", engager_user_id)

                    # use this if we only want to track the original author and the engager
                    # compare mentioned/included parent user id to original author id
                    if engager_id == author_id:
                        # print("\nTweet's Mentioned UserID: ", engager_id,
                        #       "matches original author ID: ", author_id)
                        # engager_name = engager_user["name"]
                        # engager_username = engager_user["username"]
                        # print("\nMatching Mentioned Author Name: ", engager_name)
                        # print(
                        #     "\nMatching Mentioned Author Username: ", engager_username)

                        engager_author_username = author_username

                        df = st.create_metric_dataFrame(included_id, engager_author_username,
                                                        engager_user["name"], included_likes, included_retweets,
                                                        included_replies, included_impressions, tag)

                    if engager_id == included_author_id:
                        # print("\nTweet's Mentioned UserID: ", engager_id,
                        #       "matches included/parent author ID: ", included_author_id)
                        # engager_name = engager_user["name"]
                        # engager_username = engager_user["username"]
                        # print("\nMatching Included/Parent Author Name: ",
                        #       engager_name)
                        # print(
                        #     "\nMatching Included/Parent Author Username: ", engager_username)
                        engager_author_username = included_author_username

                        df = st.create_metric_dataFrame(included_id, engager_author_username, included_author_name, included_likes,
                                                        included_retweets, included_replies, included_impressions, tag)

                export_include_df = df
                # print("\nExport Include DF: ", export_include_df)
                # print("\nExport DF: ", export_df)

                # update to use non-deprecated method
                if engine.has_table(tweetsTable) == False:
                    print("Creating table...")
                    export_include_df.to_sql(
                        tweetsTable, engine, if_exists="replace")
                    print("Table created")

                else:  # if table already exists, update or append to it
                    tweets_df = pd.read_sql_table(tweetsTable, engine)
                    # if tweet is already being tracked, update the values
                    # need to add another table that aggregates the values by user in this table
                    # that aggregated table will be what is used to make metrics based decisions
                    if engine.has_table(tweetsTable) == True and tweets_df.empty:
                        print("Table exists but is empty. Appending data...")
                        export_include_df.to_sql(
                            tweetsTable, engine, if_exists="append")
                        print("Data appended to table")

                    tweets_df = pd.read_sql_table(tweetsTable, engine)
                    if included_id in tweets_df["Tweet_ID"].values:
                        st.update_tweets_table(engine, included_id, tweets_df, included_likes,
                                               included_retweets, included_replies, included_impressions)
                    else:
                        # print("Appending to Metrics table...")
                        export_include_df.to_sql(
                            tweetsTable, engine, if_exists="append")
                        # print("New user in Metrics Table appended")

                # read the table post changes
                tweets_df = pd.read_sql_table(tweetsTable, engine)
                # print("DF Metrics Table: ", tweets_df)

                users_df = pd.read_sql_table(usersTable, engine)

                if users_df.empty:
                    # print("Users table exists but is empty. Appending data...")
                    export_users_df = pd.DataFrame(index=[included_author_username],
                                                   data=[[included_author_username, included_author_name,
                                                          included_likes, included_retweets, included_replies,
                                                          included_impressions]],
                                                   columns=["index", "Name", "Favorites",
                                                            "Retweets", "Replies", "Impressions"])
                    export_users_df.to_sql(
                        usersTable, engine, if_exists="append", index=False)
                    # print("Data appended to table")

                # if user is already being tracked, update the values in our aggregated table
                if included_author_username in users_df["index"].values:
                    st.update_aggregated_metrics(
                        engine, included_author_username, users_df, tweets_df)
                else:
                    # FIXED AUTHOR AND USERNAME NOT MATCHING FROM ROW 32 ON IN USERS_TABLE UNTIL RESET
                    # print("Appending to users table...")
                    export_users_df = pd.DataFrame(index=[included_author_username],
                                                   data=[[included_author_username, included_author_name,
                                                          included_likes, included_retweets, included_replies,
                                                          included_impressions]],
                                                   columns=["index", "Name", "Favorites",
                                                            "Retweets", "Replies", "Impressions"])
                    export_users_df.to_sql(
                        usersTable, engine, if_exists="append", index=False)
                    # print(
                    #     f"New user {included_author_name} in Users table appended (fs comment)")
                    # print("DF Users Table: ", users_df)
                    if users_df.empty == True:
                        # print("Users table is empty, appending...")
                        export_users_df.to_sql(
                            usersTable, engine, if_exists="append")
                        # print("Table appended")

                # if user is already being tracked, add them to the users table
                members_df = nft.get_db_members_collections_stats(
                    engine, config.collections, usersTable)

                wearing_list, usernames, rank_list, global_reach_list, pfpUrl_list = nft.get_wearing_list(
                    members_df)

                for user in wearing_list:
                    # ensure we update existing tables that will be used each loop
                    pfp_df = pd.read_sql_table(pfpTable, engine)
                    users_df = pd.read_sql_table(usersTable, engine)
                    rank = rank_list[wearing_list.index(user)]
                    global_reach = global_reach_list[wearing_list.index(user)]
                    pfpUrl = pfpUrl_list[wearing_list.index(user)]
                    username = usernames[wearing_list.index(user)]
                    description, url = st.get_bio_url(username)

                    # row = pfp_df.loc[pfp_df["Name"] == user]
                    # print("ROW: ", row)
                    try:
                        likes = pfp_df.loc[pfp_df["Name"]
                                           == user, "Favorites"].values[0]
                        retweets = pfp_df.loc[pfp_df["Name"]
                                              == user, "Retweets"].values[0]
                        replies = pfp_df.loc[pfp_df["Name"]
                                             == user, "Replies"].values[0]
                        impressions = pfp_df.loc[pfp_df["Name"]
                                                 == user, "Impressions"].values[0]
                    except Exception as e:
                        likes = 0
                        retweets = 0
                        replies = 0
                        impressions = 0
                        # print(
                        #     f"stuck in except of user in wearing_list loop with error {e}")

                    if user in users_df["Name"].values:
                        # print("USER NAME ENDPOINT RESPONSE: ", response.json())
                        try:
                            response = requests.get(
                                f'https://api.twitter.com/1.1/users/search.json?q={user}&count=1', auth=st.bearer_oauth)

                            username = response.json()[0]["screen_name"]
                            if response.status_code != 200:
                                print("User name endpoint failed")
                                print(response.json())
                                print(response.text)
                            if response.text == "ERROR":
                                username = users_df.loc[users_df["Name"]
                                                        == user, "index"].values[0]
                            pass
                            # continue
                        except Exception as e:
                            username = users_df.loc[users_df["Name"]
                                                    == user, "index"].values[0]
                            # print(
                            #     "stuck in except of user in users_df loop with error ", e)
                            # this could be the engager so we need to handle this better in the case the api doesnt return data
                            # OR we need to preserve the included_author_username in the users table
                            # instead of the engager as the index and propogate that change throughout the code
                            # this should help reduce api endpoint call stress as well
                        agg_likes = users_df.loc[users_df["Name"]
                                                 == user, "Favorites"].values[0]
                        agg_retweets = users_df.loc[users_df["Name"]
                                                    == user, "Retweets"].values[0]
                        agg_replies = users_df.loc[users_df["Name"]
                                                   == user, "Replies"].values[0]
                        agg_impressions = users_df.loc[users_df["Name"]
                                                       == user, "Impressions"].values[0]
                        # rank = users_df.loc[users_df["Name"]
                        #                                == user, "Rank"].values[0]
                        # global_reach = users_df.loc[users_df["Name"]
                        #                                == user, "Global_Reach"].values[0]

                        if likes < agg_likes or retweets < agg_retweets or replies < agg_replies or impressions < agg_impressions:
                            # print("Updating PFP table...")
                            st.update_pfp_tracked_table(
                                engine, pfp_df, user, username, agg_likes, agg_retweets, agg_replies, agg_impressions,
                                rank, global_reach, pfpUrl, description, url
                            )
                            description = "Reset"
                            url = "Reset"
                            print(
                                f"User {user} iterated through and updated if required\
                                    \nWaiting for next...")
                        else:
                            print(
                                f"User {user} already tracked and no updates required\
                                    \nWaiting for next...")

                    else:
                        new_pfp_user = pd.DataFrame(index=[username],
                                                    data=[
                                                        [username, user, agg_likes, agg_retweets, agg_replies, agg_impressions, rank, global_reach, pfpUrl, description, url]],
                                                    columns=["index", "Name", "Favorites",
                                                             "Retweets", "Replies", "Impressions", "Rank", "Global_Reach", "PFP_URL", "Description", "URL"])
                        new_pfp_user.to_sql(
                            pfpTable, engine, if_exists="append", index=False)

                        print(
                            f"User {user} appended to PFP table (fs comment)\
                                \nWaiting for next loop...")
                # if wearing_list != []:
                #     print("PFP DF UPDATED: ", pfp_df)


def main():
    # rules = st.get_rules()
    st.delete_all_rules(st.get_rules())
    config = Config.get_config(params)
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
