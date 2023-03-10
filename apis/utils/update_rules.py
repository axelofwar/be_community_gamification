from .stream_tools import *
import yaml

'''
Standalone file to add rules from the rules.yml file
Then run update_rules.py to update the rules on the Twitter API
Then reset the ADD_RULE in the config.yml file to 
'''


def main():
    update_rules()
    return


main()
