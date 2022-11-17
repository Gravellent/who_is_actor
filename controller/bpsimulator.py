from controller import get_profile_from_db
from models import dynamo
from common import cache, id_name_mapping, analytics_dict
import requests

def get_champion_stat(champion, position):
    if (champion, position) in analytics_dict:
        return analytics_dict[(champion, position)]
    # print("AD", analytics_dict)
    # print(champion, position)
    item = dynamo.tables['lol_analytics_table_v2'].get_item(Key={"champion_id": champion})
    if 'Item' not in item:
        return None
    res = item['Item'].get(position, None)
    analytics_dict[(champion, position)] = res
    return res

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

def get_indiviudal_matchup_win_rate(champion, position, matchup, matchup_position, item):
    if matchup_position in item and matchup in item[matchup_position]:
        stat = item[matchup_position][matchup]
        print(champion, position, matchup, matchup_position, stat['ngames'], stat['wr'])
        if stat['ngames'] < 100:
            return None
        return stat['wr']
    print(champion, matchup, 'not found!')
    return None

def calculate_win_rate(picked_players):
    win_rate = []

    for player_position, player in picked_players.items():
        if player and player != "empty":
            pair_win_rates = {}
            position = player_position[player_position.index("_")+1:]
            item = get_champion_stat(player, position)
            base_win_rate = float(item['header']['wr'])

            for matchup_position, matchup in picked_players.items():
                if player_position == matchup_position:
                    continue
                if matchup and matchup != "empty":
                    if matchup_position[:1] == player_position[:1]:
                        relation_position = "team_" + matchup_position[matchup_position.index("_")+1:]
                        matchup_win_rate = get_indiviudal_matchup_win_rate(player, position, matchup, relation_position, item)
                    else:
                        relation_position = "enemy_" + matchup_position[matchup_position.index("_") + 1:]
                        matchup_win_rate = get_indiviudal_matchup_win_rate(player, position, matchup, relation_position,
                                                                           item)
                    if matchup_win_rate is not None:
                        pair_win_rates[relation_position] = float(matchup_win_rate * 100)
                    else:
                        pair_win_rates[relation_position] = base_win_rate
                else:
                    pair_win_rates[relation_position] = base_win_rate

            if pair_win_rates:
                weights = get_weights(position)
                win_rate.append({"position": player_position,
                                "winrate": float(sum(pair_win_rates[p] * weights[p] for p in pair_win_rates))})
            else:
                win_rate.append({"position": player_position,
                                 "winrate": base_win_rate})

    print(win_rate)

    return win_rate


@cache.cached(timeout=3600, key_prefix="static_champion_data")
def get_most_recent_champion_data():
    return requests.get("http://ddragon.leagueoflegends.com/cdn/12.24.1/data/en_US/champion.json").json()['data']
