import os
# import tweepy
import yaml
import sys

'''
Tools for interacting with twitter API - single instance calls - contains functions for:
    - Initializing the twitter API
    - Getting the tweet history of a specified account for a specified number of days
    - Printing the tweet history to a file
    
The keys for the twitter API are stored in the .env file
'''

if "utils" not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    # print("Sys path: ", sys.path)
    from utils import stream_tools as st
running = True
params = st.params

# GET TWEET HISTORY BY ACCOUNT FOR DAYS SPECIFIED IN CONFIG
async def call_once(api, account, cancel):
    if not cancel:
        tweets = api.search_tweets(
            q=account, count=params.timeout)
        print("TWEET HISTORY CALLED ONCE \n")
        return tweets
    else:
        print("CANCELLED")
        return cancel


# PRINT TWEET HISTORY TO FILE
async def print_tweet_history(tweets, tweet_file):
    count = 1
    for tweet in tweets:
        # print("TWEET ", count, ": ", tweet.text)
        tweet_file.write("TWEET " + str(count) + ": " + tweet.text + "\n")
        # print("TWEET AUTHOR ", count, ": ", tweet.user.screen_name)
        tweet_file.write("TWEET AUTHOR " + str(count) +
                        ": " + tweet.user.screen_name + "\n")
        # print("TWEET TIMESTAMP ", count, ": ", tweet.created_at)
        tweet_file.write("TWEET TIMESTAMP " + str(count) +
                        ": " + str(tweet.created_at) + "\n")
        # print("TWEET LINK ", count, ": ",
        #   f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}")
        tweet_file.write("TWEET LINK " + str(count) + ": " + "https://twitter.com/" +
                        tweet.user.screen_name + "/status/" + str(tweet.id) + "\n")
        tweet_file.write("\n")
        count += 1
    return tweets
