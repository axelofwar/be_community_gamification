import asyncio
import discord
import os
import sys
from collections import Counter
import logging

'''
Tools for interacting with the Discord API - contains functions for:
    - Setting up the Discord client
    - Getting the channel history of a channel
    - Getting the messages from a channel history
    - Getting the content of a message
    - Getting the questions and keywords from messages
'''
if "utils" not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    # print("Sys path: ", sys.path)
    from utils import stream_tools as st

params = st.params


async def init_discord(cancel):
    # Create a Discord client
    if not cancel:
        intents = discord.Intents.default()
        intents.message_content = True
        client = discord.Client(intents=intents)
    else:
        logging.error("CANCELLED")
        return

    if client.is_closed():
        logging.error(f"Closed client: {client.status}")
        sys.exit()
    else:
        logging.info(f"Opened client: {client.status}")

    @client.event
    async def on_disconnect():
        logging.info(f'{client.user} has disconnected from Discord!')

    async def on_ready():
        # ensure the bot is ready and not stuck in a current activity
        logging.info("The bot is ready!\n"
                     f'{client.user} has connected to Discord!\n'
                     f'{client.user} status: {client.status}\n'
                     f'{client.user} is connected to the following guild:\n'
                     f'{client.user} current activity: {client.activity}')

    return client


# GET CHANNEL HISTORY BY ACCOUNT FOR DAYS PASSED IN
async def get_channel_history(channel_id, history_days, cancel):
    logging.info("DISCORD BOT ENTERED")
    # Create a Discord client
    if not cancel:
        client = await init_discord(cancel)
        discord_token = os.getenv("DISCORD_TOKEN")  # if using python .env file

    else:
        logging.error("CANCELLED")
        return cancel

    try:
        # start discord client
        # TODO: improve logic so that client closes on complete instead of timeout required
        if not cancel:
            task = asyncio.create_task(client.start(discord_token))
            await asyncio.wait_for(task, params.timeout)
        else:
            logging.error("TASK CANCELLED")
            sys.exit()

        logging.info(f"Client User: {client.user}")
        logging.info(f'{client.user} status: {client.status}')
        logging.info(f'{client.user} is connected to the following guild:')
        logging.info(f'{client.user} current activity: {client.activity}')
        logging.info(f"CLIENT STARTED SUCCESSFULLY {client.status}")
    except asyncio.TimeoutError:
        logging.error("CLIENT TIMEOUT")
    except discord.errors.LoginFailure as exc:
        logging.error(f'Discord Login Error: {exc}')
    except discord.errors.ClientException as exc1:
        logging.error(f'Discord Client Error: {exc1}')
    except discord.errors.HTTPException as exc2:
        logging.error(f'Discord HTTP Error: {exc2}')
    except discord.errors.DiscordException as exc4:
        logging.error(f'Discord Error: {exc4}')

    logging.info("DISCORD BOT STARTED")

    '''
    # UI LOGIC TO PROCESS CHANNEL ID USER INPUT
    if channel_id == None:
        # use channel_id from config id
        channel_value = int(config["data_channel_id"])
        logging.info("CHANNEL_VALUE: ", channel_value)
        channel = client.get_channel(channel_value)
        channel_id = channel_value
        logging.info("CHANNEL GET SUCCESS FROM NONE: ", channel)

    else:
        logging.info("CHANNEL VALUE RECIEVED: ", channel_id)
        # use channel_id passed into UI
    '''
    try:
        channel = client.get_channel(int(channel_id))
        logging.info(f"CHANNEL GET SUCCESS: {channel}")

    except:
        logging.error("CHANNEL GET FAILED")
        sys.exit()

    logging.info(f"CHANNEL HISTORY: {history_days}")
    logging.info(f"CHANNEL_ID POST: {channel_id}")
    logging.info(f"CHANNEL POST: {channel}")

    channel_history = channel.history(limit=history_days, oldest_first=True)

    # done with connection to discord
    # task.cancel()
    # TODO: fix cancel on complete so I don't need to wait whole 15 seconds
    return channel, channel_history


# GET DISCORD MESSAGES IN LOOP AND WRITE TO FILE
async def get_discord_messages(channel_history, output_file):

    async for message in channel_history:
        # process message here
        logging.debug("MESSAGE CHANNEL: %s, MESSAGE: %s, MESSAGE AUTHOR: %s, MESSAGE TIMESTAMP: %s", 
                    message.channel, message.content, message.author, message.created_at)

        link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
        # print("LINK TO MESSAGE: ", link)
        # print("\n")
        messages = []
        messages.append(message.content)
        print("DATA: ", message.content, file=output_file)
        print("AUTHOR: ", message.author, file=output_file)
        print("TIMESTAMP: ", message.created_at, file=output_file)
        print("LINK: ", link, file=output_file)
        output_file.write("\n")

    return messages, output_file

# Reset messages and questions
messages = []
questions = []


# GET POTENTIAL QUESTIONS FROM DISCORD MESSAGES
async def get_questions(chat_history):
    async for message in chat_history:
        messages.append(message.content)
        # print("MESSAGE: ", message.content)
        question_counts = Counter()
        question_words = ["what", "when", "where", "who",
                          "why", "how", "can", "could", "would", "should"]
        for word in question_words:
            if word in message.content:
                questions.append(message.content)
            question_counts[word] += message.content.lower().count(word)
        logging.debug(f"QUESTION COUNTS: {question_counts}")
        logging.debug(f"QUESTIONS: {questions}")
        top_3_questions = question_counts.most_common(3)
        logging.debug(f"Top 3 commonly asked questions: {top_3_questions}")
    return messages


# FIND KEYWORDS IN DISCORD MESSAGES
async def get_keywords(channel_history):
    async for message in channel_history:
        word_counts = Counter()
        stopwords = ["the", "and", "I", "to", "in", "a", "of", "is", "it",
                     "you", "that", "he", "was", "for", "on", "are", "as",
                     "with", "his", "they", "I'm", "at", "be", "this", "have",
                     "from", "or", "one", "had", "by", "word", "but", "not", "what",
                     "all", "were", "we", "when", "your", "can", "said", "there", "use",
                     "an", "each", "which", "she", "do", "how", "their", "if", "will",
                     "up", "other", "about", "out", "many", "then", "them", "these", "so",
                     "some", "her", "would", "make", "like", "him", "into", "time", "has",
                     "look", "two", "more", "write", "go", "see", "number", "no", "way",
                     "could", "people", "my", "than", "first", "water", "been", "call",
                     "who", "oil", "its", "now", "find", "long", "down", "day", "did",
                     "get", "come", "made", "may", "part", "<#943011412219920415>"]
        words = message.content.split()
        words = [word for word in words if word not in stopwords]
        word_counts.update(words)
        top_3_keywords = word_counts.most_common(3)
        return top_3_keywords
