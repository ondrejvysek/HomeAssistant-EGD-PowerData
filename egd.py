import json
from egd_api import EGDAPI

api = EGDAPI("client_id", "client_secret", "ean", True)
token = api.get_token()
if token:
    data = api.get_data() # see examples in egd_api.py
    if data:
        with open('c:\\0\\data.json', 'w') as f: #Change path to something
            json.dump(data, f)
