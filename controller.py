from decimal import Decimal

import boto3
import requests
import datetime

from models import dynamo
import os
import sys
from riotwatcher import LolWatcher, ApiError
import numpy as np
import sys

key=os.environ.get('RIOT_API_KEY', '')
watcher = LolWatcher(key)

def import_profile_to_db(summoner_name):
    profile = get_profile_from_name(summoner_name)['data']['leagueProfile']
    item = {
        'summoner_name': profile['summonerName'],
        'latest_ranks': profile['latestRanks'],
        'profile_icon': profile['profileIconId'],
        'puuid': profile['puuid'],
        'summoner_level': profile['summonerLevel'],
        'summoner_id': profile['summonerId'],
        'account_id': profile['accountId']
    }
    dynamo.tables['actor_users'].put_item(Item=item)
    return item['summoner_name']


def get_profile_from_db(summoner_name):
    if not summoner_name:
        return None
    item = dynamo.tables['actor_users'].get_item(Key={'summoner_name': summoner_name})
    if item and 'Item' in item:
        if 'elo' not in item['Item']:
            item['Item']['elo'] = 1200
            dynamo.tables['actor_users'].put_item(Item=item['Item'])
        return item['Item']
    else:
        return None


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


def populate_game_data_from_history(game_id):
    """
    Go through game creator's match history for 10 games to find a game from the list that matches
    :param game_id:
    :return:
    """
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']

    if 'last_update_time' in item and \
             now - datetime.datetime.fromisoformat(item['last_update_time']) < datetime.timedelta(
        minutes=2):
        print("Less than 2 min after last match history crawl...")
        return
    
    if 'match_id' in item and item['match_id']:
        update_game_info(game_id, item['match_id'])
        return

    # Search through match history
    # first_player = list(item['player_list'].keys())[0]
    # print('player', first_player)
    # puuid = dynamo.tables['actor_users'].get_item(Key={'summoner_name': first_player})['Item']['puuid']
    # match_history = get_match_history_from_puuid(puuid)
    try:
        for player in item['player_list'].keys():
            puuid = dynamo.tables['actor_users'].get_item(Key={'summoner_name': player})['Item']['puuid']
            match_history = get_match_history_from_puuid(puuid)
            match_ids = [_['id'] for _ in match_history['data']['matchlist']['matches']]
            for match_id in match_ids[:5]:
                game = watcher.match.by_id('americas', match_id)
                team100 = [_['summonerName'] for _ in game['info']['participants'] if _['teamId'] == 100]
                team200 = [_['summonerName'] for _ in game['info']['participants'] if _['teamId'] == 200]
                if (set(team100) == set(item['team1']) and set(team200) == set(item['team2'])) or (set(team100) == set(item['team2']) and set(team200) == set(item['team1'])):
                    item['match_id'] = match_id
                    if game['info']['teams'][0]['win']:
                        item['winning_team'] = 'team1'
                        item['votes'] = [None for _ in range(len(item['team1']))]
                    else:
                        item['winning_team'] = 'team2'
                        item['votes'] = [None for _ in range(len(item['team2']))]
                    dynamo.tables['actor_game'].put_item(Item=item)
                    update_game_info(game_id, match_id)
                    calculate_winning_score(game_id)
                    print('Updated:', game_id)
                    return True
    except:
        return False

    item['last_update_time'] = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    dynamo.tables['actor_game'].put_item(Item=item)


def get_profile_from_name(summoner_name):
    return requests.get(
        f'https://riot.iesdev.com/graphql?query=query%20LeagueProfile%28%24summoner_name%3AString%2C%24summoner_id%3AString%2C%24account_id%3AString%2C%24region%3ARegion%21%2C%24puuid%3AString%29%7BleagueProfile%28summoner_name%3A%24summoner_name%2Csummoner_id%3A%24summoner_id%2Caccount_id%3A%24account_id%2Cregion%3A%24region%2Cpuuid%3A%24puuid%29%7Bid%20accountId%20puuid%20summonerId%20summonerName%20summonerLevel%20profileIconId%20updatedAt%20latestRanks%7Bqueue%20tier%20rank%20wins%20losses%20leaguePoints%20insertedAt%7D%7D%7D&variables=%7B%22summoner_name%22%3A%22{summoner_name}%22%2C%22region%22%3A%22NA1%22%7D'
    ).json()

def get_match_history_from_puuid(puuid):
    return requests.get(
    'https://riot.iesdev.com/graphql?query=query%20LeagueMatchlist($region:Region!,$puuid:ID!){matchlist(region:$region,puuid:$puuid){matches{id%20playerMatch{id%20playerMatchStats{lp}}}}}&variables={%22region%22:%22NA1%22,%22puuid%22:%22' + puuid +'%22}').json()


def update_profile_match_history(profile):
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    if 'last_match_history_update_time' in profile \
            and now - datetime.datetime.fromisoformat(profile['last_match_history_update_time']) < datetime.timedelta(minutes=2):
        print("Less than 2 min after last profile update...")
    else:

        match_history = get_match_history_from_puuid(profile['puuid'])
        match_ids = iter([_['id'] for _ in match_history['data']['matchlist']['matches']])
        history = []
        matches_added = 0
        while matches_added < 20:
            match_id = next(match_ids)
            game = watcher.match.by_id('americas', match_id)
            game_duration = game['info']['gameDuration']
            game_mode = game['info']['gameMode']
            if game_mode == 'PRACTICETOOL':
                continue
            matches_added += 1
            p = [_ for _ in game['info']['participants'] if _['summonerName'] == profile['summoner_name']][0]
            history.append({
                'summoner_name': p['summonerName'],
                'game_mode': game_mode,
                'assists': p['assists'],
                'kills': p['kills'],
                'deaths': p['deaths'],
                'total_damage': p['totalDamageDealtToChampions'],
                'champion_name': p['championName'],
                'damage_per_min': Decimal(str( p['totalDamageDealtToChampions'] / game_duration * 60)),
                'cs': p['totalMinionsKilled'],
                'cs_per_min': Decimal(str( p['totalMinionsKilled'] / game_duration * 60)),
                'team_damage_percentage': Decimal(str(p['challenges'].get('teamDamagePercentage', 0))),
                'kda': Decimal(str((p['kills'] * 2 + p['assists']) / max(1, p['deaths']))),
                'win': p['win']
            })
        profile['match_history'] = history
        profile['last_match_history_update_time'] = now.replace(tzinfo=datetime.timezone.utc).isoformat()
        dynamo.tables['actor_users'].put_item(Item=profile)

    profile['solo_ranked'] = [_ for _ in profile['latest_ranks'] if _['queue'] == 'RANKED_SOLO_5X5']
    profile['flex_ranked'] = [_ for _ in profile['latest_ranks'] if _['queue'] == 'RANKED_FLEX_SR']
    if profile['solo_ranked']:
        profile['solo_ranked'] = profile['solo_ranked'][0]
        profile['solo_ranked']['tier'] = profile['solo_ranked']['tier'].capitalize()
    if profile['flex_ranked']:
        profile['flex_ranked'] = profile['flex_ranked'][0]
        profile['flex_ranked']['tier'] = profile['flex_ranked']['tier'].capitalize()
        
def add_game_to_profile(profile, item):
    if 'actor_history' not in profile:
        profile['actor_history'] = []
    
    game = watcher.match.by_id('americas', item['match_id'])
    game_duration = game['info']['gameDuration']
    p = [_ for _ in game['info']['participants'] if _['summonerName'] == profile['summoner_name']][0]
    
    profile['actor_history'].append({
        'summoner_name': p['summonerName'],
        'game_mode': 'WHO_IS_ACTOR',
        'assists': p['assists'],
        'kills': p['kills'],
        'deaths': p['deaths'],
        'total_damage': p['totalDamageDealtToChampions'],
        'champion_name': p['championName'],
        'damage_per_min': Decimal(str( p['totalDamageDealtToChampions'] / game_duration * 60)),
        'cs': p['totalMinionsKilled'],
        'cs_per_min': Decimal(str( p['totalMinionsKilled'] / game_duration * 60)),
        'team_damage_percentage': Decimal(str(p['challenges'].get('teamDamagePercentage', 0))),
        'kda': Decimal(str((p['kills'] * 2 + p['assists']) / max(1, p['deaths']))),
        'win': p['win'],
        'elo_gain': item['player_list'][p['summonerName']]['elo_gain'],
        'elo_after':item['player_list'][p['summonerName']]['elo_after']
    })
    dynamo.tables['actor_users'].put_item(Item=profile)
    

def calculate_winning_score(game_id):
    
    item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']
    winning_team = item['winning_team']
    kda = []
    item['chenghao'] = []
    
    for idx, summoner_name in enumerate(item[winning_team]):
        item['player_list'][summoner_name]['score'] = 2 # default 分数是2
        item['player_list'][summoner_name]['result'] = 'p_win'
        kda.append(item['player_list'][summoner_name]['kda'])
    max_kda_idx = np.argmax(kda).item()
    item['winning_team_max_kda_idx'] = max_kda_idx
    if max_kda_idx == item[winning_team+'_actor_idx']: #演员kda最高
        item['player_list'][item[winning_team][max_kda_idx]]['score'] = -1
        item['player_list'][item[winning_team][max_kda_idx]]['result'] = 'y_win_gxgz'
        # item['chenghao'].append('gxgz')
    else: #演员 kda不是最高
        item['player_list'][item[winning_team][max_kda_idx]]['score'] = 4
        item['player_list'][item[winning_team][max_kda_idx]]['result'] = 'p_win_max'
        item['player_list'][item[winning_team][int(item[winning_team+'_actor_idx'])]]['score'] = -3
        item['player_list'][item[winning_team][int(item[winning_team+'_actor_idx'])]]['result'] = 'y_win'
    item['player_list'][item[winning_team][max_kda_idx]]['is_max_kda'] = True
    dynamo.tables['actor_game'].put_item(Item=item)
    
def calculate_losing_score(game_id):
    item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']
    
    losing_team = 'team1' if item['winning_team'] == 'team2' else 'team2'
    kda = []
    
    for summoner_name in item[losing_team]:
        kda.append(item['player_list'][summoner_name]['kda'])
    max_kda_idx = np.argmax(kda).item()
    item['losing_team_max_kda_idx'] = max_kda_idx
    
    # count votes
    vote_received = [0] * len(item[losing_team])
    for i in range(len(item[losing_team])):
        vote_received[int(item['votes'][i])] += 1.5 if i == max_kda_idx else 1
        
    zhuojianzaichuang = int(item[losing_team+'_actor_idx']) == np.argmax(vote_received)
    
    # 投对了平民 +0，演员 -3
    if zhuojianzaichuang: # 捉奸在床
        for idx, summoner_name in enumerate(item[losing_team]):
            if idx != item[losing_team+'_actor_idx']:
                item['player_list'][summoner_name]['score'] = 0
                item['player_list'][summoner_name]['result'] = 'p_lose_zjzc'
            else:
                item['player_list'][summoner_name]['score'] = -5
                item['player_list'][summoner_name]['result'] = 'y_lose_zjzc'
        item['chenghao'].append('zjzc')
    elif max_kda_idx  != int(item[losing_team+'_actor_idx']): #蒙混过关
        for idx, summoner_name in enumerate(item[losing_team]):
            if idx != item[losing_team+'_actor_idx']:
                item['player_list'][summoner_name]['score'] = Decimal(-2.5)
                item['player_list'][summoner_name]['result'] = 'p_lose_mhgg'
            else:
                item['player_list'][summoner_name]['score'] = Decimal(4.5)
                item['player_list'][summoner_name]['result'] = 'y_lose_mhgg'
        item['chenghao'].append('mhgg')
    else: # 运筹帷幄
        for idx, summoner_name in enumerate(item[losing_team]):
            if idx != item[losing_team+'_actor_idx']:
                item['player_list'][summoner_name]['score'] = Decimal(-5)
                item['player_list'][summoner_name]['result'] = 'p_lose_ycww'
            else:
                item['player_list'][summoner_name]['score'] = Decimal(8.5)
                item['player_list'][summoner_name]['result'] = 'y_lose_ycww'
        item['chenghao'].append('ycww')
    item['player_list'][item[losing_team][max_kda_idx]]['is_max_kda'] = True
    dynamo.tables['actor_game'].put_item(Item=item)
    

def update_total_score(game_id):
    item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']
    current_item = dynamo.tables['actor_game'].get_item(Key={'game_id': item['head_game_id']})['Item']
    for username in item['player_list']:
        item['player_list'][username]['total_score'] = 0
        
    # iteratively add previous games scores
    while True:
        for username in item['player_list']:
            if username in current_item['player_list']:
                item['player_list'][username]['total_score'] += current_item['player_list'][username]['score']
        
        if current_item['next_game_id'] is None:
            break
        else:
            current_item = dynamo.tables['actor_game'].get_item(Key={'game_id': current_item['next_game_id']})['Item']
            
    dynamo.tables['actor_game'].put_item(Item=item)
    