import utils.stream_tools as st
# import yaml
from utils.config import Config

'''
Standalone file to remove rules from the rules.yml file
Then run update_rules.py to update the rules on the Twitter API
Then reset the REMOVE_RULE in the config.yml file to ""
'''


params = Config()


def main():
    config = Config.get_config(params)
    config.remove_rule = "myRule"
    config.update_rules()
    st.update_rules()


main()
