import pandas as pd
import psycopg2
import csv
import os
import subprocess
import logging
from typing import List
from pathlib import Path
from sqlalchemy import create_engine, Table, Column, Integer, Text, MetaData, select
from sqlalchemy.engine import Engine
from config import Config

from dotenv import load_dotenv
if 'GITHUB_ACTION' not in os.environ:
    load_dotenv()

'''
Tools for interacting with postgresql databases - contains functions for:
    - Connecting and creating a database
    - Creating a role
    - Writing a dataframe to a csv
    - Reading a dataframe from a csv
    - Starting our connection to the database
    - Writing a dataframe to the database
    - Getting the admin user of the database
'''

# POSTGRES CONFIG
POSTGRES_ADMIN_USER = "postgres"
# POSTGRES_USER = os.getenv("POSTGRES_USERNAME")  # github actions
# POSTGRES_USER = os.environ["POSTGRES_USERNAME"] # for local testing
POSTGRES_USER = os.getenv("DATABASE_USERNAME")  # render database

# POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")  # github actions
# POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"] # for local testing
POSTGRES_PASSWORD = os.getenv("DATABASE_PASSWORD")  # render database

# POSTGRES_HOST = os.getenv("POSTGRESQL_HOST")  # github actions
# POSTGRES_HOST = os.environ["POSTGRESQL_HOST"] # for local testing
POSTGRES_HOST = os.getenv("DATABASE_HOST")  # render database

# POSTGRES_PORT = os.getenv("POSTGRESQL_PORT")  # github actions
# POSTGRES_PORT = os.environ["POSTGRESQL_PORT"] # for local testing
POSTGRES_PORT = os.getenv("DATABASE_PORT")  # render database

create_const = "Creating Table..."

# POSTGRES SUBPROCESS FUNCTIONS
# CSV FUNCTIONS


def write_df_to_csv(df: pd.DataFrame, csv_path: Path) -> None:
    """
    Write dataframe to csv output with preset configs
    """
    df.to_csv(csv_path, index=False, quoting=csv.QUOTE_ALL)


def read_df_to_csv(csv_path: Path) -> pd.DataFrame:
    """
    Read csv values into pandas dataframe with preset configs
    """
    df = pd.read_csv(
        csv_path, index_col=0, on_bad_lines="skip")
    return df


# DATABASE ADMIN FUNCTIONS
def create_db(db_name: str, user: str) -> None:
    """
    Create PostgreSQL database if missing and assign admin user

    :param: name of database to instantiate
    :param user: the name of the user to make admin
    """
    try:
        logging.info("\nCreating database...")
        subprocess.run(["createdb", "-U", POSTGRES_ADMIN_USER,
                        "-O", user, db_name], check=True)
        logging.info("Database created")
    except subprocess.CalledProcessError:
        logging.error("Database '{}' already exists".format(db_name))


def create_role(user: str, password: str) -> None:
    """
    Create role in database for user levels in the PostgreSQL database

    :param user: the user role to create
    :param password: the password for that role
    """
    try:
        subprocess.run(
            ["createuser", "-U", POSTGRES_ADMIN_USER, user], check=True)
        logging.info("Role '{}' created.".format(user))
        subprocess.run(["psql", "-U", POSTGRES_ADMIN_USER, "-c",
                        f"ALTER USER {user} WITH PASSWORD '{password}'"], check=True)

    except subprocess.CalledProcessError:
        logging.error("Role '{}' already exists.".format(user))


# DATABASE INTERACTION FUNCTIONS
def start_db(db_name: str) -> Engine:
    """
    Instantiate and start the PostgreSQL database
    """
    engine = create_engine(
        'postgresql://'+POSTGRES_USER+':'+POSTGRES_PASSWORD+'@'+POSTGRES_HOST+':'+POSTGRES_PORT+'/'+db_name)

    return engine


# def check_metrics_table(engine: Engine, table_name: str) -> None:
#     """
#     Check the metrics table and specific members in the database -> create if missing

#     :param engine: instance connection to the PostgreSQL database
#     :param table_name: the name of the table to check
#     """
#     metadata = MetaData(bind=engine)

#     if not engine.has_table(table_name):
#         logging.info(create_const)
#         Table(table_name, metadata,
#               Column('index', Text),
#               Column('Author', Text),
#               Column('Favorites', Integer),
#               Column('Retweets', Integer),
#               Column('Replies', Integer),
#               Column('Impressions', Integer),
#               Column('Tweet_ID', Text),
#               Column('Tags', Text),
#               )
#         metadata.create_all()
#         logging.info(f"{table_name} created")
#     else:
#         logging.info(f"{table_name} Table already exists")


# def check_users_table(engine: Engine, table_name: str) -> None:
#     """
#     Check the users table and specific members -> create if missing

#     :param engine: instance connection to the PostgreSQL database
#     :param table_name: the name of the table to check
#     """
#     metadata = MetaData(bind=engine)

#     if not engine.has_table(table_name):
#         logging.info(create_const)
#         Table(table_name, metadata,
#               Column('index', Text),
#               Column('Name', Text),
#               Column('Favorites', Integer),
#               Column("Retweets", Integer),
#               Column("Replies", Integer),
#               Column("Impressions", Integer),
#               )
#         metadata.create_all()
#         logging.info(f"{table_name} created")
#     else:
#         logging.info(f"{table_name} Table already exists")


# def check_pfp_table(engine: Engine, table_name: str) -> None:
#     """
#     Check the pfp table and specific members -> create if missing

#     :param engine: instance connection to the PostgreSQL database
#     :param table_name: the name of the table to check
#     """
#     metadata = MetaData(bind=engine)

#     if not engine.has_table(table_name):
#         logging.info(create_const)
#         Table(table_name, metadata,
#               Column('index', Text),
#               Column('Name', Text),
#               Column("Favorites", Integer),
#               Column("Retweets", Integer),
#               Column("Replies", Integer),
#               Column("Impressions", Integer),
#             #   Column("Rank", Integer),
#             #   Column("Global_Reach", Integer),
#               Column("PFP_Url", Text),
#               Column("Description", Text),
#               Column("Bio_Link", Text),
#               )
#         metadata.create_all()
#         logging.info(f"{table_name} created")
#     else:
#         logging.info(f"{table_name} Table already exists")


# def check_new_pfp_table(engine: Engine, table_name: str) -> None:
#     """
#     Check the new pfp table and specific members -> create if missing

#     :param engine: instance connection to the PostgreSQL database
#     :param table_name: the name of the table to check
#     """
#     metadata = MetaData(bind=engine)

#     if not engine.has_table(table_name):
#         logging.info(create_const)
#         Table(table_name, metadata,
#               Column('index', Text),
#               Column('Name', Text),
#               Column("Favorites", Integer),
#               Column("Retweets", Integer),
#               Column("Replies", Integer),
#               Column("Impressions", Integer),
#             #   Column("Rank", Integer),
#             #   Column("Global_Reach", Integer),
#               Column("PFP_Url", Text),
#               Column("Description", Text),
#               Column("Bio_Link", Text),
#               )
#         metadata.create_all()
#         logging.info(f"{table_name} created")
#     else:
#         logging.info(f"{table_name} Table already exists")


# def check_engagement_table(engine: Engine, table_name: str) -> None:
#     """
#     Check the engagement table and specific members -> create if missing

#     :param engine: instance connection to the PostgreSQL database
#     :param table_name: the name of the table to check
#     """
#     metadata = MetaData(bind=engine)

#     if not engine.has_table(table_name):
#         logging.info(create_const)
#         Table(table_name, metadata,
#               Column('index', Text),
#               Column('Name', Text),
#               Column("Favorites", Integer),
#               Column("Retweets", Integer),
#               Column("Replies", Integer),
#               Column("Impressions", Integer),
#               Column("PFP_Url", Text),
#               Column("Description", Text),
#               Column("Bio_Link", Text),
#               )
#         metadata.create_all()
#         logging.info(f"{table_name} created")
#     else:
#         logging.info(f"{table_name} Table already exists")

def check_table(engine: Engine, table_name: str, columns: List[Column]) -> None:
    """
    Check the table and specific members in the database -> create if missing

    :param engine: instance connection to the PostgreSQL database
    :param table_name: the name of the table to check
    :param columns: list of Column objects representing the structure of the table
    """
    metadata = MetaData(bind=engine)

    if not engine.has_table(table_name):
        logging.info(create_const)
        Table(table_name, metadata, *columns)
        metadata.create_all()
        logging.info(f"{table_name} created")
    else:
        logging.info(f"{table_name} Table already exists")

def check_tables(engine: Engine, params: Config) -> None:
    check_table(engine, params.metrics_table_name, [
    Column('index', Text),
    Column('Author', Text),
    Column('Favorites', Integer),
    Column('Retweets', Integer),
    Column('Replies', Integer),
    Column('Impressions', Integer),
    Column('Tweet_ID', Text),
    Column('Tags', Text),
    ])
    check_table(engine, params.aggregated_table_name, [
    Column('index', Text),
    Column('Name', Text),
    Column('Favorites', Integer),
    Column("Retweets", Integer),
    Column("Replies", Integer),
    Column("Impressions", Integer),
    ])
    check_table(engine, params.pfp_table_name, [
    Column('index', Text),
    Column('Name', Text),
    Column("Favorites", Integer),
    Column("Retweets", Integer),
    Column("Replies", Integer),
    Column("Impressions", Integer),
    # Column("Rank", Integer),
    # Column("Global_Reach", Integer),
    Column("PFP_Url", Text),
    Column("Description", Text),
    Column("Bio_Link", Text),
    ])
    check_table(engine, params.new_pfp_table_name, [
    Column('index', Text),
    Column('Name', Text),
    Column("Favorites", Integer),
    Column("Retweets", Integer),
    Column("Replies", Integer),
    Column("Impressions", Integer),
    # Column("Rank", Integer),
    # Column("Global_Reach", Integer),
    Column("PFP_Url", Text),
    Column("Description", Text),
    Column("Bio_Link", Text),
    ])
    # check_table(engine, 'engagement_table', [
    # Column('index', Text),
    # Column('Name', Text),
    # Column("Favorites", Integer),
    # Column("Retweets", Integer),
    # Column("Replies", Integer),
    # Column("Impressions", Integer),
    # Column("PFP_Url", Text),
    # Column("Description", Text),
    # Column("Bio_Link", Text),
    # ])



def write_to_db(engine: Engine, df: pd.DataFrame, table_name: str) -> None:
    """
    Write dataframe to the database table, append if table already exists

    :param engine: instance connection to the PostgreSQL database
    :param df: the dataframe with data to add
    :param table_name: the name of the table to check
    """
    df.to_sql(table_name, engine, if_exists='append', index=True)


def get_admin_user(database_name: str):
    """
    Get the current admin user of the database

    :param database_name: (Self-explanatory)
    """
    conn = psycopg2.connect(
        host="localhost",
        database=database_name,
        user="postgres",
        password=POSTGRES_PASSWORD
    )
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pg_user")
    rows = cursor.fetchall()
    for row in rows:
        logging.debug(f"Row: {row}")


def get_all_user_metric_rows(engine: Engine, table_name: str, username: str):
    """
    Return all of the data in the metrics table for a user

    :param engine: instance connection to the PostgreSQL database
    :param table_name: the name of the table to check
    :param username: the user to get the data of

    """
    metadata = MetaData(bind=engine)
    table = Table(table_name, metadata, autoload=True)
    query = select([table]).where(table.columns.index == username)
    result = engine.execute(query)
    rows = result.fetchall()
    return rows