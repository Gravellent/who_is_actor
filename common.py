from flask_caching import Cache
import requests

cache = Cache()
id_name_mapping = {}
analytics_dict = {}


raw_data = requests.get("http://ddragon.leagueoflegends.com/cdn/13.11.1/data/en_US/champion.json").json()['data']
for k,v in raw_data.items():
    id_name_mapping[k] = v['name']