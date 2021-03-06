import celery
import requests
from app import celery
import os, json
import logging
from os import environ as env
import redis
from datetime import datetime, timedelta
from walrus import Database
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from tasks import ConsumerGroupOps

REDIS_HOST = os.getenv('REDIS_HOST',"redis")
REDIS_PORT = 6379

class PassportCredentialsGetter():
    def __init__(self):
        pass

    def get_cached_credentials(self):  
        r = redis.Redis()
        now = datetime.now()
        token_details = r.get('access_token_details')
        if token_details:    
            token_details = json.loads(token_details)
            created_at = token_details['created_at']
            set_date = datetime.strptime(created_at,"%Y-%m-%dT%H:%M:%S.%f")
            if now < (set_date - timedelta(minutes=58)):
                credentials = self.get_write_credentials()
                r.set('access_token_details', json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
            else: 
                credentials = token_details['credentials']
        else:   
            
            credentials = self.get_write_credentials()
            r.set('access_token_details', json.dumps({'credentials': credentials, 'created_at':now.isoformat()}))
            
        return credentials
            
            
    def get_write_credentials(self):        
        payload = {"grant_type":"client_credentials","client_id": env.get('PASSPORT_WRITE_CLIENT_ID'),"client_secret": env.get('PASSPORT_WRITE_CLIENT_SECRET'),"audience": env.get('PASSPORT_WRITE_AUDIENCE'),"scope": env.get('PASSPORT_AIR_TRAFFIC_SCOPE')}        
        url = env.get('PASSPORT_URL') +env.get('PASSPORT_TOKEN_URL')
        
        token_data = requests.post(url, data = payload)
        t_data = token_data.json()
        
        return t_data



# @celery.task()
# def print_hello():
#     dir(app)
    
#     with app.app_context():
#         cg = app.get_consumer_group()

#     logger = print_hello.get_logger()

#     logger.info("Hello")
    

def get_consumer_group(create=False):
    
    db = Database(host=REDIS_HOST, port =REDIS_PORT)   
    stream_keys = ['all_observations']
    
    cg = db.time_series('cg-obs', stream_keys)
    if create:
        for stream in stream_keys:
            db.xadd(stream, {'data': ''})

    if create:
        cg.create()
        cg.set_id('$')

    return cg.all_observations


@celery.task()
def submit_flights_to_spotlight():
    
    # get existing consumer group
    my_cg_ops = ConsumerGroupOps()
    cg = my_cg_ops.get_consumer_group()
    messages = cg.read()
    pending_messages = []
    
    my_credentials = PassportCredentialsGetter()
    credentials = my_credentials.get_cached_credentials()
    
    for message in messages: 
        pending_messages.append({'timestamp': message.timestamp,'seq': message.sequence, 'data':message.data, 'address':message.data['icao_address']})
    
    # sort by date
    pending_messages.sort(key=lambda item:item['timestamp'], reverse=True)

    # Keep only the latest message
    distinct_messages = {i['address']:i for i in reversed(pending_messages)}.values()
    spotlight_host = os.getenv('SPOTLIGHT_HOST', 'http://localhost:5000')
    securl = spotlight_host + '/set_air_traffic'
    headers = {"Authorization": "Bearer " + credentials['access_token']}
    for message in distinct_messages:
        payload = {"icao_address" : message['icao_address'],"traffic_source" :message['traffic_source'], "source_type" : message['source_type'], "lat_dd" : message['lat_dd'], "lon_dd" : message['lon_dd'], "time_stamp" : message['time_stamp'],"altitude_mm" : message['altitude_mm']}
        response = requests.post(securl, data= payload, headers=headers)
        logging.info(response.status_code)

