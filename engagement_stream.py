from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from utils import stream_tools as st
from utils import postgres_tools as pg
from utils import pfp_check as nft

import cv2
import json
import numpy as np
import os
import pandas as pd
import requests
import random
import time


params = st.params
engine = pg.start_db(params.db_name)
pg.check_engagement_table(engine, "engagement_table")
members = pd.DataFrame()
date_time_format = '%Y-%m-%dT%H:%M:%SZ'
matched_users, pfp_link_list, non_holders = [], [], []

# TODO: populate usernames differently than outdated table data
newpfpTable = params.new_pfp_table_name
pfp_table = pd.read_sql_table(newpfpTable, engine)
# usernames = pfp_table["index"].tolist()

# TODO: populate usernames differently than outdated table data
# this should use the live stream update method


def get_stream():
    config = params.get_config()
    next_user = "\nWaiting for next user/tweet..."
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
        members = pd.DataFrame()
        usernames = []
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
            print("\nTweet_ID: ", _id)
            tweet_data = st.get_data_by_id(_id)
            # print("Tweet Data: ", tweet_data)
            for user in tweet_data["includes"]["users"]:
                usernames.append(user["username"])
                username = user["username"]
                print("User: ", user["username"])
                name = user["name"]
                print("Name:   ", name)
                print(f"Checking user: {user['username']}...")
            try:
                pfps = st.get_profile_picture_metadata(username)
                pfp_link = pfps[0]
            except Exception as err:
                print(f"Could not get pfp for {username} with error: {err}")
                pfp_link = None
                continue

            response1 = requests.get(pfp_link)
            pfp = Image.open(BytesIO(response1.content)).convert("L")
            nft.display_image(pfp, pfp_link)

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

            # gpt4_response = "No match for this user"
            for y00t_file in random_y00ts:
                if y00t_file.endswith(".png") or y00t_file.endswith(".jpg"):
                    with open(os.path.join(y00t_folder_path, y00t_file), "rb") as f:
                        img2_data = f.read()
                        y00t = np.array(Image.open(BytesIO(img2_data)).convert(
                            "L").resize((pfp.width, pfp.height)))

                        print("\nComparing pfp to y00t image...")
                        wearing_y00t_pfp = nft.check_pfp(
                            pfp, y00t, y00t_folder_path, y00t_file)

            for degod_file in random_degods:
                if degod_file.endswith(".png") or degod_file.endswith(".jpg"):
                    with open(os.path.join(degod_folder_path, degod_file), "rb") as f:
                        img2_data = f.read()
                        degod = np.array(Image.open(BytesIO(img2_data)).convert(
                            "L").resize((pfp.width, pfp.height)))

                        print("\nComparing pfp to degod image...")
                        wearing_degod_pfp = nft.check_pfp(
                            pfp, degod, degod_folder_path, degod_file)

            if wearing_y00t_pfp[0] == True:
                print(
                    f"User {username} is wearing pfp similar to {y00t_file} or {degod_file}!")
                matched_users.append(username)
                user_info = st.get_twitter_user_info(username)
                print("\nUser Info: ", user_info)
                name = user_info["name"]
                user_id = user_info["id"]

                # Get the current time and set the start and end dates to
                # 7 days before and after the current time
                current_time = datetime.utcnow()
                start_date = (current_time - timedelta(days=params.history)
                              ).strftime(date_time_format)
                end_date = (current_time + timedelta(days=params.history)
                            ).strftime(date_time_format)
                pfp_link_list.append(pfp_link)

                metrics = st.get_user_metrics_start_end(
                    user_id, start_date, end_date)

                print("\nMetrics: ", metrics)
                bio_link, description = st.get_bio_url(username)
                member_data = pd.DataFrame(
                    [[username, name, metrics["likes"], metrics["retweets"], metrics["replies"], metrics["impressions"],
                        pfp_link, description, bio_link]])
                member_data.columns = [
                    "index", "Name", "Favorites", "Retweets", "Replies", "Impressions", "PFP_Url", "Description", "URL"]
                print("\nMember Data: ", member_data)

                # pfp_table = pd.read_sql_table(newpfpTable, engine)
                print("\nCalling update pfp tracked table...")
                st.update_engagement_table(
                    engine, "engagement_table", name, username, metrics["likes"], metrics["retweets"], metrics["replies"], metrics["impressions"], pfp_link, bio_link, description)
                members = pd.concat([members, member_data])
                print(next_user)
                # matched_ids.append(user["id"])

                # gpt4_response = gpt.chatGPTcall(
                #     model, prompt, 0.9, 1000)

                # gpt4_response = gpt.ask_GPT4(
                #     system_intel, prompt, model)
            elif wearing_degod_pfp[0] == True and wearing_y00t_pfp[0] != True:
                print(
                    f"User {username} is wearing pfp similar to {degod_file}!")
                matched_users.append(username)

                user_info = st.get_twitter_user_info(username)
                print("\nUser Info: ", user_info)
                name = user_info["name"]
                user_id = user_info["id"]

                # Get the current time and set the start and end dates to
                # 7 days before and after the current time
                current_time = datetime.utcnow()
                start_date = (current_time - timedelta(days=params.history)
                              ).strftime(date_time_format)
                end_date = (current_time + timedelta(days=params.history)
                            ).strftime(date_time_format)
                # pfp_link_list.append(pfp_link)

                metrics = st.get_user_metrics_start_end(
                    user_id, start_date, end_date)

                print("\nMetrics: ", metrics)
                bio_link, description = st.get_bio_url(username)
                member_data = pd.DataFrame(
                    [[username, name, metrics["likes"], metrics["retweets"], metrics["replies"], metrics["impressions"],
                        pfp_link, description, bio_link]])
                member_data.columns = [
                    "index", "Name", "Favorites", "Retweets", "Replies", "Impressions", "PFP_Url", "Description", "URL"]
                print("\nMember Data: ", member_data)

                # pfp_table = pd.read_sql_table(newpfpTable, engine)
                print("\nCalling update pfp tracked table...")
                st.update_engagement_table(
                    engine, "engagement_table", name, username, metrics["likes"], metrics["retweets"], metrics["replies"], metrics["impressions"], pfp_link, bio_link, description)
                members = pd.concat([members, member_data])
                print(next_user)
                # pfp_link_list.append(pfp_link)
                # matched_ids.append(user["id"])

                # gpt4_response = gpt.chatGPTcall(
                #     model, prompt, 0.9, 1000)

                # gpt4_response = gpt.ask_GPT4(
                #     system_intel, prompt, model)
            else:
                print(
                    f"User {username} is not wearing pfp similar to {y00t_file} or {degod_file}!")
                non_holders.append(username)
                print(next_user)
    print("\nMembers: ", members)


# def test():
#     user_info = st.get_twitter_user_info("axelofwar")
#     print("\nUser Info: ", user_info)
#     user_id = user_info["id"]
#     st.get_user_metrics_by_days(user_id, 7)


# test()

def main():
    # rules = st.get_rules()
    st.delete_all_rules(st.get_rules())
    config = params.get_config()
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
