# https://teadsapi.docs.apiary.io/#introduction/about-the-company

## 2021-11-20: nemam zatim osetreny zadny user msgs

# Extrac pracuje ve 2 fazi:  
# 1.  POST triggers a report
# 2.  GET to retrieve the results

import requests
import time
import json
import csv


# Load the Component library to process the config file
from keboola.component import CommonInterface
import logging

# az si jednou budu chtit vyladit error msg
# component will fail with readable message on initialization.
# REQUIRED_PARAMETERS = [KEY_PRINT_HELLO]

# init the interface
ci = CommonInterface()
# params as dictionary
params = ci.configuration.parameters

######### read user config parameter #######################

url = "https://api.teads.tv/v1/analytics/custom"
#start_date= "start_date"
#end_date= "end_date"
#dimensions_list= ["day", "placement","website","device"]
#metrics_list= ["start", "complete", "click", "impression", "teads_billing","income","firstQuartile","midpoint","thirdQuartile","publisher_sold_impression"]
#email_user= "email"
#user_token="user_token"

######### handle start / end date ###################
from dateutil.relativedelta import relativedelta
from datetime import date
import re

def ago_do_date(ago):
    value, unit = re.search(r'(\d+) (\w+) ago', ago).groups()
    if not unit.endswith('s'):
        unit += 's'
    delta = relativedelta(**{unit: int(value)})
    return(date.today() - delta)

# start date    
if 'ago' in params['start_date']:
    startdate_calc=ago_do_date(params['start_date'])
else:
    startdate_calc=params['start_date']

# end date
if 'ago' in params['end_date']:
    enddate_calc=ago_do_date(params['end_date'])
else:
    enddate_calc=params['end_date']

######### prepare the request #######################
print('Reading config:','from:',startdate_calc,'to:',enddate_calc)
print('Dimensios requested:',params['dimensions_list'])
print('Metrics requested:',params['metrics_list'])

#input to be converted to list
dimensions_list_str=params['dimensions_list']
metrics_list_str=params['metrics_list'] 

body={
"filters": {
  "date": {
      "start": startdate_calc,
      "end": enddate_calc,
      "timezone": "Europe/Berlin"
  }
},
"dimensions": dimensions_list_str.split(','),
"metrics": metrics_list_str.split(','),
#"emails": params['email'],
"format": "csv"
}

headers={'Authorization': params['#user_token'],
                       'Content-Type': 'application/json'}

######### API CALL : initiate Processing report  #######################

response = requests.post(url, data=json.dumps(body), headers=headers)
r_json= response.json()

# give user info about status 
if response.status_code == 200:
    print ('All goes well. Status = 200')
else:
    print ('Problem,status_code=',response.status_code)
    quit()


report_id=r_json['id']
status=r_json['status']
print("Report id",report_id,r_json['status'])


# wait 30sec, then check status. If 

time.sleep(30)

while status != 'finished':
    time.sleep(30)
    url_status=url+'/'+report_id
    check_report = requests.get(url=url_status, headers=headers) 
    result = check_report.json() 
    status = result['status']
    # print("Report id",report_id,status)  # just for check that id is really the same
    print(status)

else: 
    url_download = result['uri']
    print("Report id",report_id,status)



######### DOWNLOAD REPORT FROM uri (S3)  #######################
import pandas as pd

data = requests.get(url_download,timeout=10)

if data.status_code == 200:
        df = pd.read_csv(url_download, index_col=[0])

        df.to_csv('/data/out/tables/TEADS_analytics.csv')

    
       
        print("File downloaded")    

else:
        print("File download failed from".url_download)
