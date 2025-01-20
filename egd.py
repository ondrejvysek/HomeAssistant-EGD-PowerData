import json
import sys
from egd_api import EGDAPI

egdapi = EGDAPI("0287659a99ed667d4c37cc7f8011a239", "c773b8c1299972a1c11a6e9d6e1b2597", "859182400104958738", True)
token = egdapi.get_token()
if token:
    #data = api.get_data() # see examples in egd_api.py
    #data = egdapi.get_data("lastmonth", "ICC1") # see examples in egd_api.py
    dataconsumption = egdapi.get_data("ytd", "ICC1", "1.11.2024") # see examples in egd_api.py
    dataproduction = egdapi.get_data("ytd", "ISC1", "1.11.2024") # see examples in egd_api.py
    if dataconsumption:
        #print(data)
        aggregate = egdapi.sum_data(dataconsumption, "all")
        print("Consumption Total: ", aggregate['total'])
        
        aggregate_monthly = egdapi.sum_data(dataconsumption, "monthly")
        print("Consumption Monthly: ", json.dumps(aggregate_monthly))
        
        aggregate_weekly = egdapi.sum_data(dataconsumption, "weekly")
        print("Consumption Weekly: ", json.dumps(aggregate_weekly))
        
        with open('c:\\0\\data.json', 'w') as f:
            json.dump(dataconsumption, f)
    if dataproduction:
        #print(data)
        aggregate = egdapi.sum_data(dataproduction, "all")
        print("Production Total: ", aggregate['total'])
        
        aggregate_monthly = egdapi.sum_data(dataproduction, "monthly")
        print("Production Monthly: ", json.dumps(aggregate_monthly))
        
        aggregate_weekly = egdapi.sum_data(dataproduction, "weekly")
        print("Production Weekly: ", json.dumps(aggregate_weekly))
        
        with open('c:\\0\\data.json', 'w') as f:
            json.dump(dataproduction, f)
