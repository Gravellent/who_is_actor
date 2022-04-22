from models import dynamo
import os
import numpy as np
from controller import *

# constants
D = 400
K = 16
K_PLACEMENT = 32
TOTAL_PLAYERS = 8
scoring = {'zjzc': {'p_win': 0.17,
                    'p_win_max': 0.22,
                    'y_win': 0.05,
                    'y_win_gxgz': 0.1,
                    'p_lose_zjzc': 0.13,
                    'y_lose_zjzc': 0},
           'mhgg': {'p_win': 0.16,
                    'p_win_max': 0.22,
                    'y_win': 0.04,
                    'y_win_gxgz': 0.1,
                    'p_lose_mhgg': 0.06,
                    'y_lose_mhgg': 0.24},
           'ycww': {'p_win': 0.19,
                    'p_win_max': 0.24,
                    'y_win': 0.04,
                    'y_win_gxgz': 0.09,
                    'p_lose_ycww': 0,
                    'y_lose_ycww': 0.34}}



def calculate_expected_score(item, profiles, username):
    total_matchups = TOTAL_PLAYERS*(TOTAL_PLAYERS-1)/2
    total_score = 0
    
    for opponent in item['player_list'].keys():
        if username == opponent:
            continue
        
        r_i = profiles[opponent]['elo']
        r = profiles[username]['elo']
        total_score += 1/(1+10**((r_i - r)/D))
    return total_score/Decimal(total_matchups)

def update_elo(game_id):
    item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']
    
    profiles = {}
    for username in item['player_list'].keys():
        profiles[username] = get_profile_from_db(username)
        if 'elo' not in profiles[username].keys():
            
        
    new_elo = {}
    for username in item['player_list'].keys():
        expected_score = calculate_expected_score(item, profiles, username)
        actual_score = Decimal(scoring[item['chenghao'][0]][item['player_list'][username]['result']])
        # if profile in placement:
        if False:
            new_elo[username] = profiles[username]['elo'] + Decimal(PLACEMENT_K*(TOTAL_PLAYERS-1))*(actual_score - expected_score)
            item['player_list'][username]['elo_gain'] = Decimal(PLACEMENT_K*(TOTAL_PLAYERS-1))*(actual_score - expected_score)
        else:
            new_elo[username] = profiles[username]['elo'] + Decimal(K*(TOTAL_PLAYERS-1))*(actual_score - expected_score)
            item['player_list'][username]['elo_gain'] = Decimal(K*(TOTAL_PLAYERS-1))*(actual_score - expected_score)
        
        item['player_list'][username]['elo_after'] = new_elo[username]
    
    for username, profile in profiles.items():
        profile['elo'] = new_elo[username]
        dynamo.tables['actor_users'].put_item(Item=profile)
        
    dynamo.tables['actor_game'].put_item(Item=item)
        
    