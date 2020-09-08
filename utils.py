import time
import requests
from walrus import Database
from datetime import datetime, timedelta

db = Database()   
stream_keys = ['all_observations']
for stream in stream_keys:
    db.xadd(stream, {'': ''})

cg = db.time_series('cg-obs', stream_keys)
cg.create()  # Create the consumer group.
cg.set_id('$') # mark all the observations as read


def cron_worker():
    print('here')
    print(datetime.now())

def submit_flights_to_spotlight():
    
    messages = cg.all_observations.read()
    pending_messages = []
    for message in messages: 
        pending_messages.append({'timestamp': message.timestamp,'seq': message.sequence, 'data':message.data, 'address':message.data['icao_address']})
    
    # sort by date
    pending_messages.sort(key=lambda item:item['timestamp'], reverse=True)

    # Keep only the latest message
    distinct_messages = {i['address']:i for i in reversed(pending_messages)}.values()

    for message in distinct_messages:
        # headers = {}
        # payload = message
        # print(message)
        payload = {"icao_address" : message['icao_address'],"traffic_source" :message['traffic_source'], "source_type" : message['source_type'], "lat_dd" : message['lat_dd'], "lon_dd" : message['lon_dd'], "time_stamp" : message['time_stamp'],"altitude_mm" : message['altitude_mm']}
        print(payload)
        # securl = 'http://localhost:5000/set_air_traffic'
        # response = requests.post(securl, data= payload, headers=headers)


    return status

def write_incoming_data(observation):            
    msgid = cg.all_observations.add(observation)    
    now = datetime.now()    
        
    try:
        lu = db.get('last-updated')
    except KeyError as e:
        lu = None
    else: 
        lu = datetime.datetime(lu)
    
    if lu is None:
        submit_flights_to_spotlight()
    elif lu > now + timedelta(seconds=5):        
        submit_flights_to_spotlight()
        
    return msgid
