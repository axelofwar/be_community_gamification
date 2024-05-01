from dataclasses import dataclass
import os
from typing import List
from dotenv import load_dotenv
if 'GITHUB_ACTION' not in os.environ:
    load_dotenv()

@dataclass(slots=True)
class Config:
    """
    DataModel for config parameters used throughout the application

    :param add_rule: list of rules to be added to the twitter stream
    :param add_tag: list of tags to be added to the twitter stream
    :param remove_rule: list of rules to be removed from the twitter stream
    :param remove_tag: list of tags to be removed from the twitter stream
    :param account_to_query: name of account or mention to query
    :param collections: list of collection names to track 
    :param rules: the stream rules to send to the twitter get_stream endpoint
    :param tags: the stream tags to send to the twitter get_stream endpoint
    :param db_name: name of the PostgreSQL database holding engagement metrics
    :param metrics_table_name: the table holding raw metrics against users in PostgreSQL
    :param pfp_table_name: the table holding pfps and their linked users in PostgreSQL
    :param aggregated_table_name: the table holding aggregated metrics against users in PostgreSQL
    :param recount: the number of times the stream has been restarted (errors or API rate limiting)
    :param leaderboard_endpoint: the endpoint of the leaderboard with finalized metrics to be shown on the frontend
    :param database_host: the hostname of the render endpoint hosting the api
    :param update_flag: bool telling whether or not to update the stream rules
    :param timeout: the length of the timeout wait for discord (TODO: and twitter?) stream - currently just discord
    """
    add_rule: List = []
    add_tag: List = []
    remove_rule: List = []
    remove_tag: List = []
    account_to_query: str = ""
    collections: List = []
    rules: List = []
    tags: List = []
    db_name: str = "community_gamification"
    metrics_table_name: str = "metrics_table"
    pfp_table_name: str = "pfp_table" 
    new_pfp_table_name: str = "leaderboard"
    aggregated_table_name: str = "users_table"
    recount: int = 0 
    leaderboard_endpoint: str = "leaderboard"
    database_host: str = "be-community-gamification.onrender.com/api/"
    update_flag: bool = False
    timeout: int = 10
    history: int = 30

    # Retrieval functions for apis to use in the case of no local config instance at call-time
    def get_config(self):
        return self

    def set_add_rule(self, rule, tag):
        for item in rule:
            self.add_rule.append(item)
        for item in tag:
            self.add_tag.append(item)
            self.collections.append(tag)
        self.update_flag = True

    def get_add_rule(self):
        return self.add_rule

    def get_remove_rule(self):
        return self.remove_rule

    def get_add_tag(self):
        return self.add_tag

    def set_remove_rule(self, rule: str, tag: str):
        for item in rule:
            self.remove_rule.append(item)
        for item in tag:
            self.remove_tag.append(item)
            self.collections.remove(tag)
        self.update_flag = True

    def update_rules(self):
        if len(self.add_rule) > 0:
            for rule in self.add_rule:
                self.rules.append(rule)
            for tag in self.add_tag:
                self.tags.append(tag)

        if len(self.remove_rule) > 0:
            for rule in self.remove_rule:
                self.rules.remove(rule)
            for tag in self.remove_tag:
                self.tags.remove(tag)

    def get_rules(self):
        return self.rules

    def get_tags(self):
        return self.tags

    def get_metrics_table_name(self):
        return self.metrics_table_name

    def get_aggregated_table_name(self):
        return self.aggregated_table_name

    def get_pfp_table_name(self):
        return self.pfp_table_name

    def get_update_flag(self):
        return self.update_flag

    def set_update_flag(self, flag: bool):
        self.update_flag = flag

    def increment_recount(self):
        self.recount += 1

    def get_collections(self):
        return self.collections

    def add_collection_to_track(self, collection: List):
        self.collections.append(collection)
        self.update_flag = True
