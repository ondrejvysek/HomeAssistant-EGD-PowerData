import json
import sys
from egd_api import EGDAPI

egdapi = EGDAPI("client_id", "client_secret", "ean", True)
token = egdapi.get_token()
if token:
    #data = api.get_data() # get yesterday data for the ICC1 profile - see examples in egd_api.py
    #data = egdapi.get_data("lastmonth", "ICC1") # get previous month data for the ICC1 profile - see examples in egd_api.py
    dataconsumption = egdapi.get_data("ytd", "ICC1", "1.11.2024") # get data from 1.11.2024 until yesterday for ICC1 profile - see examples in egd_api.py
    dataproduction = egdapi.get_data("ytd", "ISC1", "1.11.2024") # get data from 1.11.2024 until yesterday for ISC1 profile - see examples in egd_api.py
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
