import boto3
import urllib
import json
import pandas as pd
import numpy as np
import requests
import os
import datetime
from decimal import Decimal
from tqdm import tqdm
import time

s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
bucket='lol-analytics-data-v2'
roles = ['top','jungle','middle','bottom','support']
# cids = pd.read_csv('cids.csv')
table = dynamodb.Table('lol_analytics_table_v2')
champion_static_data = requests.get("http://ddragon.leagueoflegends.com/cdn/13.11.1/data/en_US/champion.json").json()['data']

# Build a dict for map cid to champ
cid_to_champ = {}
for v in champion_static_data.values():
    cid_to_champ[int(v['key'])] = v['id']
    
def convert_match_up(l):
    return {
        cid_to_champ[_[0]]: {
            'ngames': _[1],
            'wr': Decimal(str(round(_[2] / _[1], 4)) if _[1] != 0 else 0),
        } for _ in l
    }


for k, v in tqdm(champion_static_data.items()):
    champion_id, champion_name, cid = v['id'], v['name'], v['key']
    champion_data = {
        'champion_id': champion_id,
        'cid': cid,
        'champion_name': champion_name,
        'last_update': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    for role in roles:
        key = f"data/{datetime.datetime.now().strftime('%Y-%m-%d')}/{champion_id}/{role}.json"
        obj = s3.Object(bucket, key)
        data = json.loads(obj.get()['Body'].read().decode('utf-8'), parse_float=Decimal)
        champion_data['defaultLane'] = data['header']['defaultLane']
        matchup_fields = ['enemy_top', 'enemy_jungle', 'enemy_middle', 'enemy_bottom', 'enemy_support']
        # Synergies does not include the role itself
        matchup_fields.extend([f'team_{_}' for _ in roles if _ != role]) 
        role_data = {k:convert_match_up(v) for k,v in data.items() if k in matchup_fields}
        role_data['header'] = data['header']
        champion_data[role] = role_data
    
    table.put_item(Item=champion_data)
#     time.sleep(5)