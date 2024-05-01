from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from utils import stream_tools as st
from utils import postgres_tools as pg
from utils import pfp_check as nft
from utils import chat_gpt_tools as gpt

import cv2
import json
import numpy as np
import os
import pandas as pd
import requests
import random
import time

import logging
logging.basicConfig(level=logging.INFO)

# Instance globals
params = st.params
engine = pg.start_db(params.db_name)
pg.check_engagement_table(engine, "engagement_table")
members = pd.DataFrame()
date_time_format = '%Y-%m-%dT%H:%M:%SZ'
matched_users, pfp_link_list, non_holders = [], [], []

# TODO: populate usernames differently than outdated table data
newpfpTable = params.new_pfp_table_name
pfp_table = pd.read_sql_table(newpfpTable, engine)


def get_stream():
    # Define gpt inputs for chatGPT future integration
    model = "gpt-4"
    system_intel = "You are GPT-4, answer my question as as a twitter meme and comedy expert. Your goal is to use crypto twitter relevant jokes and memes \
                            in order to generate a response that will make the user laugh and go viral. You are not allowed to use any personaly identifiable information about the user. \
                                You are not allowed to use any information about the user that is not publicly available on twitter. You can use the user's profile picture, \
                                    their username, their bio, their tweets, their followers, their following, their likes, their retweets, their quotes, their replies, \
                                        their media, their website, their birthday, their join date, their pinned tweet, their lists, and their moments. \
                                            You can also use gifs and images or short clips from the internet to generate your response. "
    config = params.get_config()
    gpt_output_file = "outputs/chatGPT_response.txt"
    next_user = "\nWaiting for next user/tweet..."
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream", auth=st.bearer_oauth, stream=True,
    )

    logging.info(f"get_stream API Status Code: {response.status_code}")

    # Error handling for various HTTP status codes
    if response.status_code == 429:
        logging.warning("TOO MANY REQUESTS - waiting 5 minutes and re-trying...")
        time.sleep(300)  # wait 5 minutes
        # waiting only 60 seconds doesn't navigate the rate limit
        get_stream()

    if response.status_code != 200:
        try:
            logging.info("Reconnecting to the stream...")
            config.recount += 1
            st.set_rules(st.delete_all_rules(st.get_rules()))
        except Exception as e:
            raise Exception(
                "Cannot get stream (HTTP {}): {}: {}".format(
                    response.status_code, response.text, e
                )
            )
    # Iterate through each response from the twitter API stream and process
    for response_line in response.iter_lines():
        members = pd.DataFrame()
        usernames = []
        if response_line:
            logging.info("\n\nGOT RESPONSE!")
            # Destroy open image windows for new comparison
            cv2.destroyAllWindows()
            if config.update_flag == True:
                logging.debug("UPDATING RULES")
                st.update_rules()
                config.update_flag = False

            json_response = json.loads(response_line)

            logging.debug(f"JSON Response: {json_response}")
            logging.debug(f"Rules tag: {json_response['matching_rules'][0]['tag']}")

            _id = json_response["data"]["id"]
            full_text = json_response["data"]["text"]

            print(f"\nTWEET_ID: {_id}; TEXT: {full_text}")
            tweet_data = st.get_data_by_id(_id)
            logging.debug(f"Tweet Data: {tweet_data}")

            # Store all users in usernames list for pfp check iteration
            for user in tweet_data["includes"]["users"]:
                usernames.append(user["username"])
                username = user["username"]
                name = user["name"]
                logging.info(f"Checking Username: {username}; Name: {name}...")
            try:
                # Get PFP metadata and determine image for validation
                pfps = st.get_profile_picture_metadata(username)
                pfp_link = pfps[0]
            except Exception as err:
                logging.warning(f"Could not get pfp for {username} with error: {err}")
                pfp_link = None
                continue

            # Store the image from the pfp_link and convert to grayscale for similarity comparison
            response1 = requests.get(pfp_link)
            pfp = Image.open(BytesIO(response1.content)).convert("L")
            nft.display_image(pfp.convert("RGB"), pfp_link)

            '''
            Take a random sample of 7 y00ts images and
            compare the structural similarity of the pfp
            to the y00ts images. Thresholds are as follows:
            - >= 0.925: 100% match
            - >= 0.90: Twinsies
            - >= 0.50: Likely in collection
            - <= 0.40: Not in collection
            '''

            # Define the folder paths for y00ts and degods images for similarity comparison
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

            # Determine if the pfp is similar to any y00ts or degods images
            # y00ts threshold = 0.5 and degods threshold = 0.45
            acceptance_threshold = .5
            for y00t_file in random_y00ts:
                if y00t_file.endswith(".png") or y00t_file.endswith(".jpg"):
                    with open(os.path.join(y00t_folder_path, y00t_file), "rb") as f:
                        img2_data = f.read()
                        y00t = np.array(Image.open(BytesIO(img2_data)).convert(
                            "L").resize((pfp.width, pfp.height)))

                        logging.info("\nComparing pfp to y00t image...")
                        wearing_y00t_pfp = nft.check_pfp(
                            pfp, y00t, y00t_folder_path, y00t_file, acceptance_threshold)

            acceptance_threshold = .45
            for degod_file in random_degods:
                if degod_file.endswith(".png") or degod_file.endswith(".jpg"):
                    with open(os.path.join(degod_folder_path, degod_file), "rb") as f:
                        img2_data = f.read()
                        degod = np.array(Image.open(BytesIO(img2_data)).convert(
                            "L").resize((pfp.width, pfp.height)))

                        logging.info("\nComparing pfp to degod image...")
                        wearing_degod_pfp = nft.check_pfp(
                            pfp, degod, degod_folder_path, degod_file, acceptance_threshold)

            # If the pfp is similar to any y00ts or degods images, then add the user to the matched_users list and update their metrics
            if wearing_y00t_pfp[0] == True:
                logging.info(
                    f"User {username} is wearing pfp similar to {y00t_file} or {degod_file}!")
                matched_users.append(username)
                user_info = st.get_twitter_user_info(username)
                logging.info(f"\nUser Info: {user_info}")
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

                # Get metrics for user from desired start to end date
                metrics = st.get_user_metrics_start_end(
                    user_id, start_date, end_date)
                logging.info(f"\nMetrics: {metrics}")

                # Determine current tweet metrics if in table for aggregation - or store new user metrics
                # Get the url/link and description/bio attached to the username provided from the tweet and store alongside member metric data
                bio_link, description = st.get_bio_url(username)
                member_data = pd.DataFrame(
                    [[username, name, metrics["likes"], metrics["retweets"], metrics["replies"], metrics["impressions"],
                        pfp_link, description, bio_link]])
                member_data.columns = [
                    "index", "Name", "Favorites", "Retweets", "Replies", "Impressions", "PFP_Url", "Description", "URL"]
                logging.info(f"\nMember Data: {member_data}")

                # pfp_table = pd.read_sql_table(newpfpTable, engine)
                # Update the engagement table with the new user metrics or metrics of existent user
                logging.info("\nCalling update pfp tracked table...")
                st.update_engagement_table(
                    engine, "engagement_table", name, username, metrics["likes"], metrics["retweets"], metrics["replies"], metrics["impressions"], pfp_link, bio_link, description)
                members = pd.concat([members, member_data])
                logging.debug(f"Next User: {next_user}")
                # matched_ids.append(user["id"])

                if logging.basicConfig(level=logging.DEBUG):
                    # Define the prompt for chatGPT for future integration
                    prompt = f"Your system intel is as follows: {system_intel} and your task is as follows: Generate a funny and potentially viral reponse to the following tweet: \n\n{full_text}\n\nUser: {user['username']}\n\n \
                            Use twitter memes, jokes, gifs, images, and other references with links from giphy to generate your response.\n\n"

                    model = "gpt-4"
                    gpt4_response = gpt.ask_gpt4(
                        system_intel, prompt, model)

                    # gpt4_response = gpt.chat_gpt_call(
                    #     model, prompt, 0.9, 5000)

                    logging.debug(f"\nGPT-4 Response: {gpt4_response}")
                    append_file = open(gpt_output_file, 'a')
                    append_file.write("\n")
                    append_file.write(f"\nUser: {name}\nResponse: {gpt4_response}")

            elif wearing_degod_pfp[0] == True and wearing_y00t_pfp[0] != True:
                logging.info(
                    f"User {username} is wearing pfp similar to {degod_file}!")
                matched_users.append(username)

                user_info = st.get_twitter_user_info(username)
                logging.info(f"\nUser Info: {user_info}")
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

                logging.info(f"\nMetrics: {metrics}")
                bio_link, description = st.get_bio_url(username)
                member_data = pd.DataFrame(
                    [[username, name, metrics["likes"], metrics["retweets"], metrics["replies"], metrics["impressions"],
                        pfp_link, description, bio_link]])
                member_data.columns = [
                    "index", "Name", "Favorites", "Retweets", "Replies", "Impressions", "PFP_Url", "Description", "URL"]
                logging.info(f"\nMember Data: {member_data}")

                logging.info("\nCalling update pfp tracked table...")
                st.update_engagement_table(
                    engine, "engagement_table", name, username, metrics["likes"], metrics["retweets"], metrics["replies"], metrics["impressions"], pfp_link, bio_link, description)
                members = pd.concat([members, member_data])
                logging.debug(f"Next User: {next_user}")
                # pfp_link_list.append(pfp_link)
                # matched_ids.append(user["id"])

                if logging.basicConfig(level=logging.DEBUG):
                    prompt = f"Your system intel is as follows: {system_intel} and your task is as follows: Generate a funny and potentially viral reponse to the following tweet: \n\n{full_text}\n\nUser: {user['username']}\n\n \
                            Use twitter memes, jokes, gifs, images, and other references to generate your response. \n\n"

                    gpt4_response = gpt.ask_gpt4(
                        system_intel, prompt, model)

                    # gpt4_response = gpt.chat_gpt_call(
                    #     model, prompt, 0.9, 5000)

                    # Write the output from the chatGPT agent to a text file for evaulation and use in the future
                    append_file = open(gpt_output_file, 'a')
                    append_file.write("\n")
                    append_file.write(f"\nUser: {name}\nResponse: {gpt4_response}")

            else:
                logging.info(
                    f"User {username} is not wearing pfp similar to {y00t_file} or {degod_file}!")
                non_holders.append(username)
                logging.info(f"Next User: {next_user}")

                if logging.basicConfig(level=logging.DEBUG):
                    prompt = f"Your system intel is as follows: {system_intel} and your task is as follows: Generate a funny and potentially viral reponse to the following tweet: \n\n{full_text}\n\nUser: {user['username']}\n\n \
                            Use twitter memes, jokes, gifs, images, and other references to generate your response. \n\n"

                    gpt4_response = gpt.ask_gpt4(
                        system_intel, prompt, model)

                    # Write the output from the chatGPT agent to a text file for evaulation and use in the future
                    append_file = open(gpt_output_file, 'a')
                    append_file.write("\n")
                    append_file.write(f"\nUser: {name}\nResponse: {gpt4_response}")

                # gpt4_response = gpt.chat_gpt_call(
                #     model, prompt, 0.9, 5000)

    logging.info(f"\nMembers: {members}")


# def test():
#     user_info = st.get_twitter_user_info("axelofwar")
#     print("\nUser Info: ", user_info)
#     user_id = user_info["id"]
#     st.get_user_metrics_by_days(user_id, 7)


# test()

def main():
    # rules = st.get_rules()
    # Get the current stream rules from the twitter API and delete them for reset
    st.delete_all_rules(st.get_rules())
    # Get the desired stream rules from the config and add them to the twitter API
    config = params.get_config()
    config.history = 30  # number of days to track back tweet metrics
    config.set_add_rule(["y00ts", "DeGods"], ["y00ts", "degods"])
    config.update_rules()
    st.set_rules()
    ''' Example of adding a rule for a collection -
     edit this through ssh to add more collections'''
    # config.set_add_rule("CryptoPunks", "cryptopunks")
    # config.update_rules()
    # st.set_rules()

    # Activate the stream and begin processing new tweets matching the desired rules
    get_stream()


if __name__ == "__main__":
    main()
