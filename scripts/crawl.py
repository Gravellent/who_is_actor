import boto3
import urllib
import json
import pandas as pd
import numpy as np
import requests
import os
import datetime
from tqdm import tqdm

version = "1"
patch = "30" # Change to last 30 days
roles = ['top','jungle','middle','bottom','support']
team_roles = ['team_top', 'team_jungle', 'team_middle', 'team_bottom', 'team_support']
headers = {'User-Agent' : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"}
s3 = boto3.resource('s3')
BUCKET = "lol-analytics-data-v2"

champion_static_data = requests.get("http://ddragon.leagueoflegends.com/cdn/13.11.1/data/en_US/champion.json").json()['data']


for k, v in tqdm(champion_static_data.items()):
    champion_id, champion_name, cid = v['id'], v['name'], v['key']
    
    for role in roles:
        url = "https://axe.lolalytics.com/mega/?ep=champion&p=d&v="+version+"&patch="+patch+"&cid="+str(cid)+"&lane="+role+"&tier=gold_plus&queue=420&region=all"
        resp = requests.get(url, headers=headers)
        data = resp.json()
        
        # The second URL is queried to find syngeries with champs on the same team
        url2 = "https://axe.lolalytics.com/mega/?ep=champion2&p=d&v="+version+"&patch="+patch+"&cid="+str(cid)+"&lane="+role+"&tier=gold_plus&queue=420&region=all"
        resp2 = requests.get(url2, headers=headers)
        data2 = resp2.json()
        for team_role in team_roles:
            if team_role in data2:
                data[team_role] = data2[team_role]
        with open('tmp.json', 'w') as f:
            f.write(json.dumps(data))
        s3.Bucket(BUCKET).upload_file("tmp.json", f"data/{datetime.datetime.now().strftime('%Y-%m-%d')}/{champion_id}/{role}.json")
        os.remove('tmp.json')
#     break
