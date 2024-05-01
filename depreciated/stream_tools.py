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
    from utils.config import Config
else:
    from utils.config import Config


params = Config()

def update_aggregated_metrics(engine: Engine, 
                              author_username: str, 
                              users_df: pd.DataFrame, 
                              tweets_df: pd.DataFrame) -> None:
    """
    DEPRECIATED: Get the aggregated metrics for a user across the tweets metrics table

    :param engine: the instance connection to the PostgreSQL database
    :param author_username: the username of the author to track
    :param users_df: the dataframe holding users to check against (no repeats)
    :param tweets_df: the dataframe holding tweet metrics to aggregate per user (repeats = new tweet same user)

    TODO: Confirm that the update_aggregated_metrics function is \
        working as intended. It should only update rows that have changed \
            and not the entire table. We still need to confirm if the += logic \
                being using to aggregate the values is correct.  \
                    It should be from observation but need verifiable testing
    """
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
        logging.info(
            f"Aggregated values for {author_username} in Users table updated")
    else:
        logging.info(f"No changes to aggregated values for {author_username}")

def update_tweets_table(engine: Engine, 
                        id: str, 
                        tweets_df: pd.DataFrame, 
                        included_likes: int, 
                        included_retweets: int, 
                        included_replies: int, 
                        included_impressions: int):
    """
    DEPRECIATED: Update the tweets table with new tweet metric data from a known/unknown user

    :param engine: the instance connection to the PostgreSQL database
    :param id: the ID of the tweet for unique tracking and updating
    :param tweets_df: the dataframe holding tweet metrics to update (repeats = same tweet new metrics)
    :param included_likes: the number of likes the ID'd tweet has
    :param included retweets: the number of rewteets the ID'd tweet has
    :param included replies: the number of replies the ID'd tweet has
    :param included impressions: the number of impressions the ID'd tweet has

    TODO: Confirm that the update_tweets_table function is working properly \
        this method should only update the values in the table if they have increased \
            If it isn't then use then investigate more heuristic method of updating the table
    """
    config = Config.get_config(params)
    tweets_table = config.get_metrics_table_name()
    logging.info(
        f"Tweet #{id} already exists in Metrics table +\
        \nUpdating Metrics table...")
    # get the row that needs to be updated
    row = tweets_df.loc[tweets_df["Tweet_ID"] == id]
    row = row.values[0]

    # drop unnecessary columns if present
    if len(row) > 6:
        row = row[1:]
        if "level_0" in tweets_df.columns:
            logging.warning("DAMNIT LEVEL_0")
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
        logging.info(f"Metrics Likes updated to {included_likes}")
        tweets_df.loc[tweets_df["Tweet_ID"] ==
                      id, ["Favorites"]] = included_likes
        updated_metrics["Favorites"] = included_likes

    if int(included_retweets) > int(retweets):
        logging.info(f"Metrics Retweets updated to {included_retweets}")
        tweets_df.loc[tweets_df["Tweet_ID"] ==
                      id, ["Retweets"]] = included_retweets
        updated_metrics["Retweets"] = included_retweets

    if int(included_replies) > int(replies):
        logging.info(f"Metrics Replies updated to {included_replies}")
        tweets_df.loc[tweets_df["Tweet_ID"] ==
                      id, ["Replies"]] = included_replies
        updated_metrics["Replies"] = included_replies

    if int(included_impressions) > int(impressions):
        logging.info(f"Metrics Impressions updated to {included_impressions}")
        tweets_df.loc[tweets_df["Tweet_ID"] == id,
                      ["Impressions"]] = included_impressions
        updated_metrics["Impressions"] = included_impressions

    # update only the rows that have changed - sql query
    if updated_metrics:
        logging.info(f"Updating Tweets Table with updated metrics: {updated_metrics}")
        engine.execute(f"""
            UPDATE {tweets_table}
            SET {','.join([f'"{k}" = {v}' for k,v in updated_metrics.items()])}
            WHERE "Tweet_ID" = '{id}'
        """)  # extra ' after f is needed to uppercase the column names

    # drop unnecessary columns if present
    if "level_0" in tweets_df.columns:
        logging.warning("DAMNIT LEVEL_0 LOL")
        tweets_df.drop(columns=["level_0"], inplace=True)

    logging.info("Metrics table updated")

def update_engagement_table(engine: Engine, 
                            name: str, 
                            username: str, 
                            agg_likes: int, 
                            agg_retweets: int, 
                            agg_replies: int, 
                            agg_impressions: int, 
                            pfp_url: str, 
                            desc: str, 
                            url: str):
    """
    DEPRECIATED FUNCTION for updating engagement table (now metrics table)

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

    TODO: remove once other operations confirmed
    """
    # config = Config.get_config(params)
    # pfp_table_name = config.get_pfp_table_name() # temp commented out
    logging.info("Updating PFP Tracked Table...")
    # check if the user is already in the table
    pfp_table_name = "engagement_table"  # temp added
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
            # hard set these each time as they are harder to compare than values and should be fine to override
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
                "PFP_Url": [pfp_url],
                "Description": [desc],
                "Bio_Link": [url]
            })
            pfp_table = pfp_table._append(new_row, ignore_index=True)
            pfp_table.to_sql(pfp_table_name, engine,
                             if_exists="replace", index=False)
            logging.info(f"User {username} added to {pfp_table_name}")
    return pfp_table

def create_dataFrame(id, author_username, author_name, likes, retweets, replies, impressions):
    """
    DEPRECIATED: Function for creating a basic data frame - depreciated because each table has unique frame struct
    
    TODO: consolidate frames so that a generic like this can be used
    """
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
