# from celery.schedules import crontab
from datetime import timedelta
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

HEARTBEAT = os.getenv('HEARTBEAT_RATE_SECS',5)
imports = ['blender.tasks.blend', 'tasks']
result_expires = 30

accept_content = ['json', 'msgpack', 'yaml']
task_serializer = 'json'
result_serializer = 'json'

beat_schedule = {
    'submit-spotlight': {
        'task': 'blender.tasks.blend.submit_flights_to_spotlight',
        # Every 30 secionds
        'schedule': timedelta(seconds=int(HEARTBEAT)),
    }, 
    
    # 'poll-flights':{
    #     'task': 'blender.tasks.flights_reader.poll_uss_for_flights',
    #     # Every 30 secionds
    #     'schedule': timedelta(seconds=int(HEARTBEAT)),
        
    # }
}