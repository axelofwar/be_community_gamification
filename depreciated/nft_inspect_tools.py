from time import sleep
# import postgres_tools as pg
# import stream_tools as st

import requests
import pandas as pd
# import yaml
from utils.config import Config

'''
Tools for interacting with the NFTInspect API - contains functions for:
    - Getting the collection members
    - Getting the collection data
    - Getting the collection members data
    - Getting the collection members data frame
'''

# with open("utils/yamls/config.yml", "r") as f:
#     config = yaml.load(f, Loader=yaml.FullLoader)
config = Config()


def add_collection_to_track(collection):
    Config.get_config()

    # Add collection to track
    # with open("utils/yamls/config.yml", "r") as f:
    #     config = yaml.safe_load(f)

    if collection not in config.collections:
        config.append_collections(collection)
    else:
        print(f"{collection} already in config class")

    # with open("utils/yamls/config.yml", "w") as f:
    #     yaml.dump(config, f)

    return


def remove_collection_to_track(collection):
    Config.get_config()

    # Remove collection to track
    # with open("utils/yamls/config.yml", "r") as f:
    #     config = yaml.safe_load(f)

    if collection in config.get_collections():
        config.collections.remove(collection)
    else:
        print(f"{collection} not found in config class")

    # with open("utils/yamls/config.yml", "w") as f:
    #     yaml.dump(config, f)

    return


def get_simple_members(collection):
    response = requests.get(
        f"https://www.nftinspect.xyz/api/collections/members/{collection}?limit=7500&onlyNewMembers=false"
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get user data (HTTP {}): {}".format(
                response.status_code, response.text)
        )

    output = response.json()
    # print("Output: ", output)
    members = output["members"]
    for member in members:
        name = member["name"]
        username = member["username"]
        rank = member["rank"]
        reach = member["globalReach"]
        pfpUrl = member["pfpUrl"]

        # print(
        #     f"Member {name} has rank: {rank} and global reach: {reach} with pfp url: {pfpUrl}")

    return members


def get_members(engine, collection, usersTable):
    response = requests.get(
        f"https://www.nftinspect.xyz/api/collections/members/{collection}?limit=7500&onlyNewMembers=false"
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get user data (HTTP {}): {}".format(
                response.status_code, response.text)
        )

    output = response.json()
    members = output["members"]

    members_data_frame = pd.DataFrame(
        {
            "Name": [],
            "Username": [],
            "Wearing PFP": [],
            "PFP URL": [],
            "Global_Reach": [],
            "Rank": [],
            "Time With Token": [],
            "Time With Collection": [],
        }
    )

    names = []
    users_df = pd.read_sql_table(usersTable, engine)
    for name in users_df["Name"]:
        names.append(name)

    for member in members:
        member_name = member["name"]
        member_username = member["username"]
        member_wearing_pfp = member["isWearingCollectionsPfp"]
        member_pfp_url = member["pfpUrl"]
        member_global_reach = member["globalReach"]
        member_rank = member["rank"]
        member_time_with_token = member["timeWithToken"]
        member_time_with_collection = member["timeWithCollection"]

        member_data_frame = pd.DataFrame(
            {
                "Name": [member_name],
                "Username": [member_username],
                "Wearing PFP": [member_wearing_pfp],
                "PFP URL": [member_pfp_url],
                "Global_Reach": [member_global_reach],
                "Rank": [member_rank],
                "Time With Token": [member_time_with_token],
                "Time With Collection": [member_time_with_collection],
            }
        )

        members_data_frame = pd.concat(
            [members_data_frame, member_data_frame])

    # print(f"{collection} data frame: \n", members_data_frame, "\n")

    return members_data_frame


def get_collection_members(engine, collection, usersTable):
    response = requests.get(
        f"https://www.nftinspect.xyz/api/collections/members/{collection}?limit=7500&onlyNewMembers=false"
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get user data (HTTP {}): {}".format(
                response.status_code, response.text)
        )

    output = response.json()
    members = output["members"]
    # ranks = output["rank"]

    members_data_frame = pd.DataFrame(
        {
            "Name": [],
            "Username": [],
            "Wearing PFP": [],
            "PFP URL": [],
            "Global_Reach": [],
            "Rank": [],
            "Time With Token": [],
            "Time With Collection": [],
        }
    )

    names = []
    users_df = pd.read_sql_table(usersTable, engine)
    for name in users_df["Name"]:
        names.append(name)

    for member in members:
        member_name = member["name"]
        member_username = member["username"]
        member_wearing_pfp = member["isWearingCollectionsPfp"]
        member_pfp_url = member["pfpUrl"]
        member_global_reach = member["globalReach"]
        member_rank = member["rank"]
        member_time_with_token = member["timeWithToken"]
        member_time_with_collection = member["timeWithCollection"]

        member_data_frame = pd.DataFrame(
            {
                "Name": [member_name],
                "Username": [member_username],
                "Wearing PFP": [member_wearing_pfp],
                "PFP URL": [member_pfp_url],
                "Global_Reach": [member_global_reach],
                "Rank": [member_rank],
                "Time With Token": [member_time_with_token],
                "Time With Collection": [member_time_with_collection],
            }
        )
        # TODO: overwrite y00ts in table to use the correct pfp instead of a degod

        if member_name in names:
            # print(
            # f"Member {member_name} in users_df database - check if wearing PFP")
            members_data_frame = pd.concat(
                [members_data_frame, member_data_frame])

    # print(f"{collection} data frame: \n", members_data_frame, "\n")

    return members_data_frame


def get_db_members_collections_stats(engine, collections, usersTable):
    # print("Collections :", collections, "\n")
    m_tot_df = pd.DataFrame()
    for collection in collections:
        sleep(0.25)
        m_df = get_collection_members(engine, collection, usersTable)
        m_tot_df = pd.concat([m_tot_df, m_df])
        # print("Collection :", collection, "iterated and completed...\n")
    # print(m_tot_df)
    return m_tot_df


def get_wearing_list(members_df):
    wearing_list, rank_list, global_reach_list, pfpUrl_list, user_names = [], [], [], [], []
    _iter = 0

    # print("MEMBERS DF: ", members_df, "\n")
    for member in members_df["Name"].values:
        # print("Member :", member, "\n")
        # print("Wearing PFP :", members_df["Wearing PFP"].values[_iter], "\n")
        # print(f "Member {member} Wearing PFP :", bool(members_df["Wearing PFP"].values[iter]),
        #   "\n")
        if members_df["Wearing PFP"].values[_iter] > 0:
            # print(
            #     f"{member} pfp check successful - add/update to pfp_table", "\n")
            wearing_list.append(member)
            user_names.append(members_df["Username"].values[_iter])
            rank_list.append(members_df["Rank"].values[_iter])
            # print("Rank :", members_df["Rank"].values[iter], "\n")
            global_reach_list.append(
                members_df["Global_Reach"].values[_iter]*100)
            # print("Global Reach % :", members_df["Global Reach"].values[iter]*100,
            #       "\n")
            pfpUrl_list.append(members_df["PFP URL"].values[_iter])
        else:
            pass
            # print(f"{member} pfp check failed - skip", "\n")
        _iter += 1
    # print(f"Members wearing PFP: {wearing_list}", "\n")
    return wearing_list, user_names, rank_list, global_reach_list, pfpUrl_list


'''
The functions below are for standalone use of the nft_inspect_tools.py file
'''


# def main():
# get_simple_members("y00ts")
# #     engine = pg.start_db(config["db_name"])
# #     add_collection_to_track("bonkz")
# #     tot_df = get_db_members_collections_stats(
# #         engine, config["collections"], config["aggregated_table_name"])
# #     remove_collection_to_track("bonkz")

# #     get_wearing_list(tot_df)


# main()
