import datetime
from models import dynamo
from decimal import Decimal
import os
from riotwatcher import LolWatcher, ApiError


#key = os.environ.get('RIOT_API_KEY', '')
key = "RGAPI-d234d085-3a8e-4c29-a400-f5285286dd7a"
watcher = LolWatcher(key)

def update_game_info(game_id, riot_game_id):
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})
    if not item:
        return
    item = item['Item']
    if 'last_update_time' in item and \
             now - datetime.datetime.fromisoformat(item['last_update_time']) < datetime.timedelta(
        minutes=2):
        print("Less than 2 min after last game update...")
        return

    try:
        game = watcher.match.by_id('americas', riot_game_id)
    except:
        print("Riot API error")

    for p in game['info']['participants']:
        item['player_list'][p['summonerName']]['assists'] = p['assists']
        item['player_list'][p['summonerName']]['kills'] = p['kills']
        item['player_list'][p['summonerName']]['deaths'] = p['deaths']
        item['player_list'][p['summonerName']]['total_damage'] = p['totalDamageDealtToChampions']
        item['player_list'][p['summonerName']]['champion_name'] = p['championName']
        item['player_list'][p['summonerName']]['kda'] = Decimal(str((p['kills'] * 2 + p['assists']) / max(1, p['deaths'])))
    item['last_update_time'] = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    dynamo.tables['actor_game'].put_item(Item=item)
