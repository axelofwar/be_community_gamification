import os
from dotenv import load_dotenv
if 'GITHUB_ACTION' not in os.environ:
    load_dotenv()


# class Config:
#     def __init__(self):
#         self.add_rule = ""
#         self.add_tag = ""
#         self.remove_rule = ""
#         self.account_to_query = ""
#         self.collections = []
#         self.rules = []
#         self.tags = []
#         self.db_name = "community_gamification"
#         self.metrics_table_name = "metrics_table"
#         self.pfp_table_name = "pfp_table"
#         self.aggregated_table_name = "users_table"
#         self.recount = 0
#         self.leaderboard_endpoint = "leaderboard"
#         self.database_host = "be-community-gamification.onrender.com/api/"
#         self.update_flag = False
class Config:
    def __init__(self, add_rule="", add_tag="", remove_rule="", account_to_query="", collections=[], rules=[], tags=[], db_name="community_gamification", metrics_table_name="metrics_table", pfp_table_name="pfp_table", aggregated_table_name="users_table", recount=0, leaderboard_endpoint="leaderboard", database_host="be-community-gamification.onrender.com/api/", update_flag=False):
        self.add_rule = add_rule
        self.add_tag = add_tag
        self.remove_rule = remove_rule
        self.account_to_query = account_to_query
        self.collections = collections
        self.rules = rules
        self.tags = tags
        self.db_name = db_name
        self.metrics_table_name = metrics_table_name
        self.pfp_table_name = pfp_table_name
        self.aggregated_table_name = aggregated_table_name
        self.recount = recount
        self.leaderboard_endpoint = leaderboard_endpoint
        self.database_host = database_host
        self.update_flag = update_flag

    def get_config(self):
        return self

    def set_add_rule(self, rule, tag):
        self.add_rule = rule
        self.add_tag = tag
        self.collections.append(tag)
        self.update_flag = True

    def get_add_rule(self):
        return self.add_rule

    def get_remove_rule(self):
        return self.remove_rule

    def get_add_tag(self):
        return self.add_tag

    def set_remove_rule(self, rule):
        self.remove_rule = rule
        self.update_flag = True

    def update_rules(self):
        if self.add_rule != "":
            self.rules.append(self.add_rule)
            self.tags.append(self.add_tag)

        if self.remove_rule != "":
            self.rules.remove(self.remove_rule)

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

    def set_update_flag(self, flag):
        self.update_flag = flag

    def increment_recount(self):
        self.recount += 1

    def get_collections(self):
        return self.collections

    def append_collections(self, collection):
        self.collections.append(collection)

    def add_collection_to_track(self, collection):
        self.collections.append(collection)
        self.update_flag = True
