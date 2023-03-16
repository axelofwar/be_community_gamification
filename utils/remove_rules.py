import stream_tools as st
# import yaml
from config import Config

'''
Standalone file to remove rules from the rules.yml file
Then run update_rules.py to update the rules on the Twitter API
Then reset the REMOVE_RULE in the config.yml file to ""
'''

config = Config.get_config()
if config.get_config() is None:
    config = Config()


def main():
    config.set_remove_rule("myRule")
    config.update_rules()
    st.update_rules()
    return


main()
