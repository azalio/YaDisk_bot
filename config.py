import configparser

config = configparser.ConfigParser()
config.read('config.ini')

# telegram
token = config['telegram']['token']

# mongodb
host = config['mongo']['host']
port = config['mongo']['port']
db = config['mongo']['db']
collection = config['mongo']['collection']

# yamaps
yamaps_key = config['yamaps']['key']

# yadisk
app_id = config['yadisk']['app_id']
