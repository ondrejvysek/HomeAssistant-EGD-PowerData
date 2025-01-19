import json
from egd_api import EGDAPI

api = EGDAPI("0287659a99ed667d4c37cc7f8011a239", "c773b8c1299972a1c11a6e9d6e1b2597", "859182400104958738")
token = api.get_token()
if token:
    data = api.get_data() # see examples in egd_api.py
    if data:
        with open('c:\\0\\data.json', 'w') as f: #Change path to something
            json.dump(data, f)
