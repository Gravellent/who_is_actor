from controller import get_profile_from_db
from models import dynamo
from common import cache, id_name_mapping, analytics_dict
import requests

# @cache.cached(timeout=1200, key_prefix="champion_stat")
def get_champion_stat(champion, position):
    if (champion, position) in analytics_dict:
        return analytics_dict[(champion, position)]
    item = dynamo.tables['lol_analytics_table'].get_item(Key={"champion": champion})
    if 'Item' not in item:
        return None
    res = item['Item'].get(position, None)
    analytics_dict[(champion, position)] = res
    return res

def get_paginated_chmapion_icon(exclude=[]):
    number_per_row = 12
    champions = [{
        "name": v['name'],
        "id": k,
    } for k, v in get_most_recent_champion_data().items()]
    champions = [_ for _ in champions if _["id"] not in exclude]
    champions = sorted(champions, key=lambda x: x["name"])
    res = []
    for i in range(len(champions) // number_per_row):
        batch = []
        for j in range(number_per_row):
            batch.append(champions[number_per_row*i + j])
        res.append(batch)
    return res

def add_champion_to_pool(username, position, champion_id):
    profile = get_profile_from_db(username)
    if 'champion_pool' not in profile:
        profile['champion_pool'] = {}
    if position not in profile['champion_pool']:
        profile['champion_pool'][position] = set()
    if champion_id not in profile['champion_pool'][position]:
        profile['champion_pool'][position].add(champion_id)
    dynamo.tables['actor_users'].put_item(Item=profile)

def delete_champion_from_pool(username, position, champion_id):
    profile = get_profile_from_db(username)
    if 'champion_pool' not in profile:
        return
    if position not in profile['champion_pool']:
        return
    if champion_id in profile['champion_pool'][position]:
        profile['champion_pool'][position].remove(champion_id)
    dynamo.tables['actor_users'].put_item(Item=profile)

def get_champion_pool(username, position):
    profile = get_profile_from_db(username)
    if 'champion_pool' not in profile:
        return []
    if position not in profile['champion_pool']:
        return []
    return sorted(list(profile['champion_pool'][position]))

def calculate_win_rate(position, champion_pool, picked_players):
    win_rate = []
    for c in champion_pool:
        pair_win_rates = []
        item = dynamo.tables['lol_analytics_table'].get_item(Key={"champion": id_name_mapping[c]})['Item'][position]
        for matchup_position, matchup in picked_players.items():
            if matchup and matchup != "empty":
                matchup_win_rate = get_indiviudal_matchup_win_rate(c, position, matchup, matchup_position, item)
                if matchup_win_rate is not None:
                    pair_win_rates.append(matchup_win_rate * 100)
        base_win_rate = float(item['header']['wr'])
        average_win_rate = float(sum(pair_win_rates) / len(pair_win_rates)) if pair_win_rates else base_win_rate
        win_rate.append({
            'id': c,
            'win_rate': average_win_rate,
            'base_win_rate': base_win_rate,
            'delta': average_win_rate - base_win_rate,
        })
    return win_rate

def get_indiviudal_matchup_win_rate(champion, position, matchup, matchup_position, item):
    if matchup_position in item and matchup in item[matchup_position]:
        stat = item[matchup_position][matchup]
        print(champion, position, matchup, matchup_position, stat['ngames'], stat['wr'])
        return stat['wr']
    print(champion, matchup, 'not found!')
    return None

@cache.cached(timeout=3600, key_prefix="static_champion_data")
def get_most_recent_champion_data():
    return requests.get("http://ddragon.leagueoflegends.com/cdn/12.9.1/data/en_US/champion.json").json()['data']
