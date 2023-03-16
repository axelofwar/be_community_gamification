import os
from dotenv import load_dotenv
if 'GITHUB_ACTION' not in os.environ:
    load_dotenv()


class Config:
    def __init__(cls):
        cls.add_rule = ""
        cls.add_tag = ""
        cls.remove_rule = ""
        cls.account_to_query = ""
        cls.collections = []
        cls.rules = []
        cls.tags = []
        cls.db_name = "community_gamification"
        cls.metrics_table_name = "metrics_table"
        cls.pfp_table_name = "pfp_table"
        cls.aggregated_table_name = "users_table"
        cls.recount = 0
        cls.leaderboard_endpoint = "leaderboard"
        cls.database_host = "be-community-gamification.onrender.com/api/"
        cls.update_flag = False

    @classmethod
    def get_config(cls):
        return cls

    @classmethod
    def set_add_rule(cls, rule, tag):
        cls.add_rule = rule
        cls.add_tag = tag
        cls.update_flag = True

    @classmethod
    def get_add_rule(cls):
        return cls.add_rule

    @classmethod
    def get_remove_rule(cls):
        return cls.remove_rule

    @classmethod
    def get_add_tag(cls):
        return cls.add_tag

    @classmethod
    def set_remove_rule(cls, rule):
        cls.remove_rule = rule
        cls.update_flag = True

    @classmethod
    def update_rules(cls):
        if cls.add_rule != "":
            cls.rules.append(cls.add_rule)
            cls.tags.append(cls.add_tag)

        if cls.remove_rule != "":
            cls.rules.remove(cls.remove_rule)

    @classmethod
    def get_rules(cls):
        return cls.rules

    @classmethod
    def get_tags(cls):
        return cls.tags

    @classmethod
    def get_metrics_table_name(cls):
        return cls.metrics_table_name

    @classmethod
    def get_aggregated_table_name(cls):
        return cls.aggregated_table_name

    @classmethod
    def get_pfp_table_name(cls):
        return cls.pfp_table_name

    @classmethod
    def get_update_flag(cls):
        return cls.update_flag

    @classmethod
    def set_update_flag(cls, flag):
        cls.update_flag = flag

    @classmethod
    def increment_recount(cls):
        cls.recount += 1

    @classmethod
    def get_collections(cls):
        return cls.collections

    @classmethod
    def append_collections(cls, collection):
        cls.collections.append(collection)

    @classmethod
    def add_collection_to_track(cls, collection):
        cls.collections.append(collection)
        cls.update_flag = True
