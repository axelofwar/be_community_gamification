import json
import os
import pandas as pd
import requests
from dotenv import load_dotenv
import time
import cv2
import numpy as np
from utils import stream_tools as st
from utils import postgres_tools as pg
# from utils import nft_inspect_tools as nft
from utils import pfp_check as nft
from utils import chat_gpt_tools as gpt
from utils.config import Config
from PIL import Image
from io import BytesIO
import random


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


def display_image(img1, pfp_link):
    img1_cv = np.array(img1)
    img1_cv = cv2.cvtColor(img1_cv, cv2.COLOR_BGR2RGB)
    img1_cv = cv2.resize(img1_cv, (500, 500))
    cv2.imshow(f"Image {pfp_link}", img1_cv)
    cv2.waitKey(1)


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
            cv2.destroyAllWindows()
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
            pfp_link_list, matched_users, matched_ids, non_holders = [], [], [], []
            members = pd.DataFrame()
            print("\nTweet_ID: ", _id)
            tweet_data = st.get_data_by_id(_id)
            # print("Tweet Data: ", tweet_data)
            for user in tweet_data["includes"]["users"]:
                pfps = st.get_profile_picture_metadata(
                    user["username"])
                pfp_link = pfps[0]
                print("Username: ", user["username"])

                response1 = requests.get(pfp_link)
                pfp = Image.open(BytesIO(response1.content)).convert("L")
                display_image(pfp, pfp_link)

                '''
                Take a random sample of 7 y00ts images and
                compare the structural similarity of the pfp
                to the y00ts images. Thresholds are as follows:
                - >= 0.925: 100% match
                - >= 0.90: Twinsies
                - >= 0.50: Likely in collection
                - <= 0.40: Not in collection
                '''
                y00t_folder_path = "outputs/y00ts_imgs"
                degod_folder_path = "outputs/degods_imgs"
                y00t_filenames = [f for f in os.listdir(
                    y00t_folder_path) if f.endswith(("png", "jpg"))]
                degod_filenames = [f for f in os.listdir(
                    degod_folder_path) if f.endswith(("png", "jpg"))]
                random_y00ts = random.sample(
                    y00t_filenames, min(5, len(y00t_filenames)))
                random_degods = random.sample(
                    degod_filenames, min(5, len(degod_filenames)))

                gpt4_response = "No match for this user"
                for y00t_file in random_y00ts:
                    # for filename in os.listdir(folder_path):
                    for degod_file in random_degods:
                        if y00t_file.endswith(".png") or y00t_file.endswith(".jpg"):
                            with open(os.path.join(y00t_folder_path, y00t_file), "rb") as f:
                                img2_data = f.read()
                                y00t = np.array(Image.open(BytesIO(img2_data)).convert(
                                    "L").resize((pfp.width, pfp.height)))

                                wearing_y00t_pfp = nft.check_pfp(
                                    pfp, y00t, y00t_folder_path, y00t_file)

                        if degod_file.endswith(".png") or degod_file.endswith(".jpg"):
                            with open(os.path.join(degod_folder_path, degod_file), "rb") as f:
                                img2_data = f.read()
                                degod = np.array(Image.open(BytesIO(img2_data)).convert(
                                    "L").resize((pfp.width, pfp.height)))

                                wearing_degod_pfp = nft.check_pfp(
                                    pfp, degod, degod_folder_path, degod_file)

                    system_intel = "You are GPT-4, answer my question as as a twitter meme and comedy expert. Your goal is to use crypto twitter relevant jokes and memes \
                            in order to generate a response that will make the user laugh and go viral. You are not allowed to use any personaly identifiable information about the user. \
                                You are not allowed to use any information about the user that is not publicly available on twitter. You can use the user's profile picture, \
                                    their username, their bio, their tweets, their followers, their following, their likes, their retweets, their quotes, their replies, \
                                        their media, their website, their birthday, their join date, their pinned tweet, their lists, and their moments. \
                                            You can also use gifs and images or short clips from the internet to generate your response. "

                    prompt = f"Your system intel is as follows: {system_intel} and your task is as follows: Generate a funny and potentially viral reponse to the following tweet: \n\n{full_text}\n\nUser: {user['username']}\n\n \
                        Use twitter memes, jokes, gifs, images, and other references to generate your response. \n\n"

                    model = "gpt-3.5-turbo-0301"
                    # model = "gpt-4-32k"
                    print("Wearing Y00t PFP: ", wearing_y00t_pfp)
                    print("Wearing Degod PFP: ", wearing_degod_pfp)
                    if wearing_y00t_pfp[0] == True:
                        print(
                            f"User {user['username']} is wearing pfp similar to {y00t_file} or {degod_file}!")
                        matched_users.append(user["username"])
                        matched_ids.append(user["id"])

                        gpt4_response = gpt.chatGPTcall(
                            model, prompt, 0.9, 1000)

                        # gpt4_response = gpt.ask_GPT4(
                        #     system_intel, prompt, model)
                        break
                    elif wearing_degod_pfp[0] == True:
                        print(
                            f"User {user['username']} is wearing pfp similar to {degod_file}!")
                        matched_users.append(user["username"])
                        matched_ids.append(user["id"])

                        gpt4_response = gpt.chatGPTcall(
                            model, prompt, 0.9, 1000)

                        # gpt4_response = gpt.ask_GPT4(
                        #     system_intel, prompt, model)
                        break
                    else:
                        print(
                            f"User {user['username']} is not wearing pfp similar to {y00t_file} or {degod_file}!")
                        non_holders.append(user["username"])

                pfp_link_list.append(pfp_link)

            # set default table before each read
            pfp_table = pd.read_sql_table(newpfpTable, engine)
            print("PFP List: ", pfp_link_list)
            for username in matched_users:
                print("Username: ", username)
                print("User already in database")
                # update metrics
                metrics = st.get_user_metrics_by_days(
                    matched_ids[matched_users.index(username)], params.history)
                print("Metrics: ", metrics)
                bio_link, description = st.get_bio_url(username)
                member_data = pd.DataFrame(
                    [[username, user["name"], metrics["likes"], metrics["retweets"], metrics["replies"], metrics["impressions"],
                      pfp_link_list[matched_users.index(username)], description, bio_link]])
                member_data.columns = [
                    "index", "Name", "Favorites", "Retweets", "Replies", "Impressions", "PFP_Url", "Description", "URL"]
                print("Member Data: ", member_data)

                pfp_table = pd.read_sql_table(newpfpTable, engine)
                print("Calling update pfp tracked table...")
                st.update_pfp_tracked_table(
                    engine, pfp_table, user["name"], username, metrics["likes"], metrics["retweets"], metrics["replies"], metrics["impressions"], pfp_link_list[matched_users.index(username)], description, bio_link)
                members = pd.concat([members, member_data])

            for non_holder in non_holders:
                if non_holder in pfp_table["index"].values:
                    print("Non holder already in database")
                    pfp_table = pfp_table.drop(
                        pfp_table[pfp_table["index"] == non_holder].index)
                    pfp_table.to_sql(
                        newpfpTable, engine, if_exists="replace", index=False)
                else:
                    print("Non holder not in database")

            if gpt4_response != "No match for this user":
                print("Sending response to tweet...")
                print("Response: ", gpt4_response)

            # determine ways to get rank, reach, and pfp status
            # nft-inspect api may be limiting/blocking my ip address
            '''
            totals = pd.DataFrame()
            total_members = pd.DataFrame()
            for collection in params.collections:
                print("Collection: ", collection)
                # total_members = nft.get_members(engine, collection, usersTable)

                totals = pd.concat([totals, total_members])

            # see all the dudes in nft inspect datatbase wearing pfps and the metadata of the twitter image
            # for dude in totals["Name"]:
            #     if totals["Wearing PFP"][totals["Name"] == dude].values[0] == True:
            #         time.sleep(5)
            #         # print("Dude is wearing PFP: ", dude)
            #         thisUrl, thisMetadta = st.get_profile_picture_metadata(
            #             totals["Username"][totals["Name"] == dude].values[0])

            #         with open("outputs/pfp_metadata.txt", "a") as f:
            #             f.write(
            #                 f"{dude} is wearing NFT with metadata: {thisMetadta}\n")
            #         print(
            #             f"User {dude} is wearing NFT {thisUrl}with metadata: {thisMetadta}\n")

            
            wearing_list, usernames, rank_list, global_reach_list, pfpUrl_list = nft.get_wearing_list(
                totals)

            non_holders = []
            memebers = pd.DataFrame(
                columns=["index", "Name", "Favorites", "Retweets", "Replies", "Impressions",
                         "Rank", "Global_Reach", "PFP_URL", "Description", "Bio_Link"]
            )
            '''

            '''

            if tweet_data["includes"] and "tweets" in tweet_data["includes"]:
                print("Users: ", tweet_data["includes"]["users"])
                for user in tweet_data["includes"]["users"]:
                    # print("Author: ", user)
                    name = user["name"]
                    username = user["username"]
                    # if user["name"] in wearing_list:
                    # pfpurl, metadata = st.get_profile_picture_metadata(
                    #     username)
                    # print(
                    #     f"User {name}, username {username} is wearing NFT with metadata: {metadata}")
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
                                "replies"], metrics["impressions"], rank, global_reach, pfp_url, description, url
                        )
                        # print("Member Data: ", member_data)
                        memebers = pd.concat([memebers, member_data])
                    else:
                        print("Updating non holders...")
                        non_holders.append(user["username"])
                        pfp_table = pd.read_sql_table(newpfpTable, engine)
                        if user["name"] in pfp_table["Name"].values:
                            # remove from pfp table
                            print(
                                "No longer wearing PFP - Removing from pfp table...")
                            pfp_table = pfp_table[pfp_table["Name"]
                                                  != user["name"]]
                            pfp_table.to_sql(
                                newpfpTable, engine, if_exists="replace")
                        else:
                            print("Not in pfp table, skipping...")

                print("Holders: ", memebers["Name"].values.tolist())
                print("Non Holders: ", non_holders)
                '''

            '''
                TODO:
                - determine why frank and y00ts are not in the list of holders
                - determine if we can get pfp metadata without nft inspect
                - determine why y00ts have the wrong pfp
            '''


def main():
    # rules = st.get_rules()
    st.delete_all_rules(st.get_rules())
    config = Config.get_config(params)
    config.history = 30  # number of days to track back tweet metrics
    config.set_add_rule(["y00ts", "DeGods"], ["y00ts", "degods"])
    config.update_rules()
    # config.set_add_rule("DeGods", "degods")
    # config.update_rules()
    ''' Example of adding a rule for a collection -
     edit this through ssh to add more collections'''
    # config.set_add_rule("CryptoPunks", "cryptopunks")
    # config.update_rules()
    st.set_rules()
    get_stream()


if __name__ == "__main__":
    main()
