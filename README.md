# Axelofwar X (Twitter) Stream Bot

### Environment Setup
1. If you don’t have Python installed, [install it from here](https://www.python.org/downloads/) OR

- **LINUX**:

```bash
$ sudo apt-get install python3
```

- **MAC**:

```bash
$ brew install python
```

- **WINDOWS**: gotta use the website + .exe lol

2. Install OpenAI

- `pip install openai`
> - **Note:** OpenAI is ONLY used for discord bot responses and twitter stream in DEBUG mode

3. Clone this repository


4. Navigate into the project directory

   ```bash
   $ cd be_community_gamification
   ```

5. Create a new virtual environment

   ```bash
   $ python -m venv venv
   $ . venv/bin/activate
   ```

6. Install the requirements

   ```bash
   $ pip install -r requirements.txt
   ```

### Copy and populate .env

7. Make a copy of the example environment variables file

   ```bash
   $ cp .env.example .env
   ```

8. Add your [OpenAI API key](https://beta.openai.com/account/api-keys) to the newly created `.env` file

9. Add your [Twitter API keys](https://developer.twitter.com/en/portal/dashboard) to the `.env` file

10. Add your [Discord token](https://discord.com/developers/applications) to the `.env` file
- **Note:** Only add discord token if using `discord_tools`

11. Add your [postgresql](https://www.postgresql.org/) credentials (use [pgAdmin4](https://www.pgadmin.org/) for gui db interaction) to the `.env` file. Also add the RENDER credentials where applicable for the database hosted non-locally
    > - `POSTGRESQL_HOST` -> localhost (change as required)
    > - `POSTGRESQL_PORT` -> 5433 (change as required 5432 = default)

- `POSTGRES_USER` -> username of your database table owner
- `POSTGRES_PASSWORD` -> password of your database table owner

### Populate config.yml with values for desired Twitter stream
12. Edit `config.yml` with desired run parameters - the most important are:

- `ADD_RULE` -> add a mention or @ to track
- `ADD_TAG` -> update the tag for which all tweets matching the rule will be stored under
- `REMOVE_RULE` -> remove a mention or @ to track
- `account_to_query` -> primary twitter account to track mentions of on init
- `db_name` -> the name of your database or postgresql server
- `table_name` -> the name of the table in your database or server
- `chat_channel_id` -> default channel if none is entered in UI or permissions not attained (lower case) - this is used to query the questions and user inptus
- `data_channel_id` -> this is the channel to use in order to answer the question
- `tweet_history` -> number of tweets from archive you want to pull (more = longer process time)
- `prompt` -> details of what question you want to ask chatGPT

13. Create db and table (if not present) - use [pgAdmin4](https://www.pgadmin.org/) for easiest interaction OR use [postgresql](https://www.postgresql.org/) if comfortable.

- `config.yml` -> update **db_name** and **table_name** to values from previous step

### In pgAdmin4 or postgresql:

14. Create server on `localhost:5433/` with your `db name`, `username`, and `password`

15. Populate the `metrics_table_name` and `aggregated_table_name` with your database values in `config.yml`

You can follow the pgadmin4 steps to setup your own - or you can import `df_table.csv` to your postgresql server (untested)

#

# Run steps by use case

You should now see three .txt files as well as terminal outputs, the .txt files are labeled appropriately:

1. Run the app for twitter listener bot + database update

```bash
$ python3 stream.py
```

2. Start the database api

```bash
$ cd be-community-gamification
$ python3 manage.py runserver
```

3. Start the frontend connecting to the db api (currently on localhost)

```bash
$ cd fe-community-gamification
$ npm run dev
```

4. **OPTIONAL:** Update rules while running stream - in
    `config.yml`:

- update `ADD_RULE`: with your @account or #tag to add
- update `ADD_TAG`: with the project name/tag

```bash
$ python3 utils/update_rules.py
```

5. **OPTIONAL** Remove rules while running stream - in
    `config.yml`:

- update `REMOVE_RULE`: with your @account or #tag to remove

```bash
$ python3 utils/remove_rules.py
```

#

## NOTES

### stream.py:

The 3 primary areas for improvement are:
1. Replace ssim image comparison logic with something more scalable and efficient
2. Update all uses of nft-inspect API with our own methods
3. Add rate limitng and websockets to API for more efficient fronend

Standalone functions for testing individual operation can be found in `/standalone` and will continue to be fleshed out.

### Table tracking:
There are three user's currently identified in the tweet tracking logic of stream.py

- `author` = originator of the tweet being tracked
- `included` = the author of the tweet included (retweeted, quoted, replied to, mentioned, etc.)
- `engager` = currently should return the same as the above two - as well as any other accounts mentioned in the tweet.
  > _engager_ could be used in the future to reward all users mentioned instead of just author + engager
  > it is currently used to confirm that the author of the included tweet is indeed that author - could be used to reward tweet being engaged more than engager via multiplier as decided.

There are 6 columns in the table - all self explanatory expect:

- `index` = engager @username
- `author` = included author's display name
- `Tweet ID` = id used to track and aggregate metrics per tweet

#
## OpenAI API Quickstart - Python example app

Here is an example pet name generator app used in the OpenAI API [quickstart tutorial](https://beta.openai.com/docs/quickstart). It uses the [Flask](https://flask.palletsprojects.com/en/2.0.x/) web framework. Check out the tutorial or follow the instructions below to get set up. This example was stripped as a starting place for this project.
