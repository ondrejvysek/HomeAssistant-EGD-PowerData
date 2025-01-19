# EGD CZ API for retrieving energy data
# Example usage:
# api = EGDAPI(client_id="your_client_id", client_secret="your_client_secret", meter_id="your_meter_id", debug=True)
# token = api.get_token()
# if token:
#     data = api.get_data() # get yesterday's data
#     data = api.get_data("thisweek") # get this week's data
#     data = api.get_data("lastweek", "ICQ2") # get last week's data for profile ICQ2 (produced energy)
#     data = api.get_data("interval", "ICC1", "20.1.2023", "26.1.2023") # get data for a custom interval with ICC1 profile (consumed energy)
#     print(data)
# Valid profile options:
#   ICC1 - Činná spotřeba ze sítě čtvrthodinová - výkon (kW) *Použito pro fakturaci
#   ICQ2 - Činná spotřeba ze sítě čtvrthodinová - energie (kWh)
#   ISC1 - Činná dodávka do sítě (přetok) čtvrthodinová - výkon (kW) *Použito pro fakturaci
#   ISQ2 - Činná dodávka do sítě (přetok) čtvrthodinová - energie (kWh)
#   ICCS - Spotřeba pokrytá z vůdčího odběrného místa čtvrthodinová (kWh)
#   * Hodnoty v kW odpovídají střednímu čtvrthodinovému výkonu. Po součtu za období se nerovnají energii v kWh. Pro přepočet na kWh je potřeba hodnoty vydělit čtyřmi. 
# Valid interval options: yesterday (Default), thisweek, lastweek, thismonth, lastmonth, thisyear, ytd, interval
#   "interval" - requires start_date and end_date to be specified with the format day.month.year no time included (e.g. 25.1.2023)
#   "ytd" - year to date. Enter start date, end date is yesterday
### TODO:
# 1. sum functions all data, daily, weekly, monthly

import requests
from dateutil import tz
from datetime import datetime, timedelta
from colorama import Fore, Style

class EGDAPI:
    url_data = "https://data.distribuce24.cz/rest/spotreby"
    url_token = "https://idm.distribuce24.cz/oauth/token"

    def __init__(self, client_id, client_secret, meter_id, debug=False):
        self.client_id = client_id
        self.client_secret = client_secret
        self.meter_id = meter_id
        self.access_token = None
        self.debug = debug
        self.debug_print("EGDAPI object created", "SUCCESS")

    def debug_print(self, message, severity=None):
        if self.debug:
            if severity == "ERROR":
                print(f"{Fore.RED}{message}{Style.RESET_ALL}")
            elif severity == "SUCCESS":
                print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")
            else:
                print(message)

    def get_token(self):
        # Define the payload for the POST request to get the token
        payload_token = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "namerena_data_openapi"
        }
        # Define the headers for the POST request
        headers_token = {
            "Content-Type": "application/json"
        }
        # Make the POST request to get the token
        response_token = requests.post(self.url_token, json=payload_token, headers=headers_token, allow_redirects=True)
        # Check if the request was successful
        if response_token.status_code < 400:
            # Parse the JSON response
            token_data = response_token.json()
            self.access_token = token_data.get("access_token")
            self.debug_print("Access token retrieved successfully", "SUCCESS")
            return self.access_token
        else:
            self.debug_print(f"Failed to get token: {response_token.status_code} - {response_token.text}", "ERROR")
            return None

    def get_data(self, interval="yesterday", profile="ICC1", start_date=None, end_date=None):

        # Calculate start_date and end_date based on the interval
        today = datetime.today()
        if interval == "yesterday":
            start_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
            end_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        elif interval == "thisweek":
            start_date = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
            end_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        elif interval == "lastweek":
            start_date = (today - timedelta(days=today.weekday() + 7)).strftime('%Y-%m-%d')
            end_date = (today - timedelta(days=today.weekday() + 1)).strftime('%Y-%m-%d')
        elif interval == "thismonth":
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            end_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        elif interval == "lastmonth":
            first_day_of_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            last_day_of_last_month = today.replace(day=1) - timedelta(days=1)
            start_date = first_day_of_last_month.strftime('%Y-%m-%d')
            end_date = last_day_of_last_month.strftime('%Y-%m-%d')
        elif interval == "thisyear":
            start_date = today.replace(month=1, day=1).strftime('%Y-%m-%d')
            end_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        elif interval == "ytd":
            if not start_date:
                self.debug_print("Year to date interval requires start_date to be specified.", "ERROR")
                return None
            try:
                start_date = datetime.strptime(start_date, "%d.%m.%Y").strftime('%Y-%m-%d')
            except ValueError:
                self.debug_print("Invalid date format. Please use day.month.year format.", "ERROR")
                return None
            end_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        elif interval == "interval":
            if not start_date or not end_date:
                self.debug_print("Custom interval requires both start_date and end_date.", "ERROR")
                return None
            # Parse the custom date strings in the format day.month.year
            try:
                start_date = datetime.strptime(start_date, "%d.%m.%Y").strftime('%Y-%m-%d')
                end_date = datetime.strptime(end_date, "%d.%m.%Y").strftime('%Y-%m-%d') + " 23:45:00"
            except ValueError:
                self.debug_print("Invalid date format. Please use day.month.year format.", "ERROR")
                return None
        else:
            self.debug_print("Invalid interval specified.", "ERROR")
            return None

        # add time to the date 00:00:00.000Z and 23:45:00.000Z
        start_date = start_date + "T00:00:00.000Z"
        end_date = end_date + "T23:45:00.000Z"
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S.000Z")
            end_date = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.000Z")
        except ValueError:
            self.debug_print(f"Invalid date format. Please use day.month.year format. {Fore.RED}Do not add time to the date.{Style.RESET_ALL}", "ERROR")
            return None
        utc_stime = start_date.astimezone(tz.tzutc()).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        utc_etime = end_date.astimezone(tz.tzutc()).strftime('%Y-%m-%dT%H:%M:%S.000Z')        
        self.debug_print(f"Start date: {start_date}")
        self.debug_print(f"End date: {end_date}")
        self.debug_print(f"UTC Start date: {utc_stime}")
        self.debug_print(f"UTC End date: {utc_etime}")
        
        # Check if the access token is available
        if not self.access_token:
            self.debug_print("Access token is missing. Please get the token first.", "ERROR")
            return None
        # Define the headers for the GET request
        headers_data = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        # Define the parameters for the GET request
        params_data = {
            "ean": self.meter_id,
            "from": utc_stime,
            "to": utc_etime,
            "profile": profile,
            "pageSize": "3000"
        }
        self.debug_print(f"Data parameters: {params_data}")
        all_data = []
        unique_data = []
        unique_timestamps = set()
        page_number = 1 # Start with the first page
        while True:
            # Update the page number in the parameters
            params_data["pageStart"] = str(page_number)
            self.debug_print(f"Executing Page number: {page_number}")
            # Make the GET request to fetch the data
            response_data = requests.get(self.url_data, headers=headers_data, params=params_data)
            # Check if the request was successful
            if response_data.status_code < 400:
                # Parse the JSON response
                data = response_data.json()
                if not data:
                    break
                if isinstance(data, list) and len(data) > 0:
                    first_record = data[0]
                    if 'total' in first_record:
                        total = first_record['total']
                    else:
                        self.debug_print(f"Error: 'total' field not found in the response.", "ERROR")
                        break
                else:
                    self.debug_print(f"Error: Unexpected response structure.", "ERROR")
                    break 
                self.debug_print(f"Iteration: {page_number} Total records: {total}")               
                # Append the data to the list
                all_data.extend(data)
                if total < 3000:  # If the returned data is less than pageSize, we've reached the last page
                    break                
                page_number += 1
            else:
                self.debug_print(f"Failed to get data: {response_data.status_code} - {response_data.text}", "ERROR")
                break

        if all_data:
            self.debug_print("Data retrieved successfully", "SUCCESS")
            return all_data
        else:  
            self.debug_print("No data found.", "ERROR")
            return None
