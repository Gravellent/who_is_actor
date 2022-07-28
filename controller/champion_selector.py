from controller import get_profile_from_db
from models import dynamo
from common import cache, id_name_mapping, analytics_dict
import requests
import json
import math

@cache.memoize(3600)
def get_champion_stat(champion, position):
    item = dynamo.tables['lol_analytics_table_v2'].get_item(Key={"champion_id": champion})
    if 'Item' not in item:
        return None
    res = item['Item'].get(position, None)
    analytics_dict[(champion, position)] = res
    return res

def chunkify(l, chunk_size):
    return [l[i:i + chunk_size] for i in range(0, len(l), chunk_size)]

def get_paginated_chmapion_icon(exclude=[], default_lane="all"):
    number_per_row = 12
    if default_lane == "all":
        champions = [{
            "name": v['name'],
            "id": k,
        } for k, v in get_most_recent_champion_data().items()]
    else:
        champions = [{
            "name": v['name'],
            "id": k,
        } for k, v in get_most_recent_champion_data().items() if v['default_lane'] == default_lane]

    champions = [_ for _ in champions if _["id"] not in exclude]
    champions = sorted(champions, key=lambda x: x["name"])
    return chunkify(champions, 12)

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
        if len(profile['champion_pool'][position]) == 1:
            profile['champion_pool'].pop(position)
        else:
            profile['champion_pool'][position].remove(champion_id)
    dynamo.tables['actor_users'].put_item(Item=profile)

def get_champion_pool(username, position):
    profile = get_profile_from_db(username)
    if 'champion_pool' not in profile:
        return []
    if position not in profile['champion_pool']:
        return []
    return sorted(list(profile['champion_pool'][position]))

def get_weights(position):
    if position == "top":
        weights = {
            'team_top': 0,
            'team_jungle': 0.08,
            'team_middle': 0.08,
            'team_bottom': 0.05,
            'team_support': 0.04,
            'enemy_top': 0.5,
            'enemy_jungle': 0.09,
            'enemy_middle': 0.07,
            'enemy_bottom': 0.05,
            'enemy_support': 0.04
        }
    elif position == "jungle":
        weights = {
            'team_top': 0.11,
            'team_jungle': 0,
            'team_middle': 0.13,
            'team_bottom': 0.07,
            'team_support': 0.11,
            'enemy_top': 0.11,
            'enemy_jungle': 0.17,
            'enemy_middle': 0.12,
            'enemy_bottom': 0.07,
            'enemy_support': 0.11
        }
    elif position == "middle":
        weights = {
            'team_top': 0.07,
            'team_jungle': 0.13,
            'team_middle': 0,
            'team_bottom': 0.07,
            'team_support': 0.07,
            'enemy_top': 0.05,
            'enemy_jungle': 0.1,
            'enemy_middle': 0.4,
            'enemy_bottom': 0.06,
            'enemy_support': 0.05
        }
    elif position == "bottom":
        weights = {
            'team_top': 0.03,
            'team_jungle': 0.05,
            'team_middle': 0.1,
            'team_bottom': 0,
            'team_support': 0.24,
            'enemy_top': 0.03,
            'enemy_jungle': 0.05,
            'enemy_middle': 0.1,
            'enemy_bottom': 0.2,
            'enemy_support': 0.2
        }
    elif position == "support":
        weights = {
            'team_top': 0.03,
            'team_jungle': 0.05,
            'team_middle': 0.1,
            'team_bottom': 0.2,
            'team_support': 0,
            'enemy_top': 0.03,
            'enemy_jungle': 0.05,
            'enemy_middle': 0.1,
            'enemy_bottom': 0.2,
            'enemy_support': 0.24
        }
    return weights

def calculate_win_rate(position, champion_pool, picked_players):
    win_rate = []
    for c in champion_pool:

        if c in list(picked_players.values()):
            continue

        pair_win_rates = {}
        item = get_champion_stat(c, position)
        base_win_rate = float(item['header']['wr'])
        for matchup_position, matchup in picked_players.items():
            if matchup and matchup != "empty":
                matchup_win_rate = get_indiviudal_matchup_win_rate(c, position, matchup, matchup_position, item)
                if matchup_win_rate is not None:
                    pair_win_rates[matchup_position] = float(matchup_win_rate * 100)
                else:
                    pair_win_rates[matchup_position] = base_win_rate
            else:
                pair_win_rates[matchup_position] = base_win_rate
        if pair_win_rates:
            weights = get_weights(position)
            average_win_rate = float(sum(pair_win_rates[p] * weights[p] for p in pair_win_rates))
        else:
            average_win_rate = base_win_rate

        delta = average_win_rate - base_win_rate
        delta = 0 if math.isclose(delta, 0, abs_tol=1e-9) else delta
        win_rate.append({
            'id': c,
            'win_rate': average_win_rate,
            'base_win_rate': base_win_rate,
            'delta': delta
        })
    return sorted(win_rate, key=lambda x: (x['delta'], x['win_rate']), reverse=True)

def get_top3_matchup(position, champion_pool, picked_players):
    top3_matchup = {}

    for matchup_position, matchup in picked_players.items():
        if matchup and matchup != "empty":
            champion_win_rate = {}
            for c in champion_pool:
                if c in list(picked_players.values()):
                    continue
                item = get_champion_stat(c, position)
                base_win_rate = float(item['header']['wr'])
                matchup_win_rate = get_indiviudal_matchup_win_rate(c, position, matchup, matchup_position, item)
                if matchup_win_rate is not None:
                    delta = float(matchup_win_rate * 100)-base_win_rate
                else:
                    continue
                champion_win_rate[c] = delta
            top3_matchup[matchup_position] = sorted(champion_win_rate, key=champion_win_rate.get, reverse=True)[:3]
        else:
            top3_matchup[matchup_position] = []

    return top3_matchup


def get_indiviudal_matchup_win_rate(champion, position, matchup, matchup_position, item):
    if matchup_position in item and matchup in item[matchup_position]:
        stat = item[matchup_position][matchup]
        print(champion, position, matchup, matchup_position, stat['ngames'], stat['wr'])
        if stat['ngames'] < 100:
            return None
        return stat['wr']
    print(champion, matchup, 'not found!')
    return None

@cache.cached(timeout=3600, key_prefix="static_champion_data")
def get_most_recent_champion_data():
    with open('./static/champ_lane.json', 'r') as f:
        champ_lane_mapping = json.loads(f.read())
    data = requests.get("http://ddragon.leagueoflegends.com/cdn/12.13.1/data/en_US/champion.json").json()['data']
    for k in data:
        data[k]['default_lane'] = champ_lane_mapping[k]
    return data
