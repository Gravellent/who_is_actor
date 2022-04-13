from decimal import Decimal

import boto3
import requests
import datetime

from models import dynamo
import os
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
        'account_id': profile['accountId'],
    }
    dynamo.tables['actor_users'].put_item(Item=item)
    return item['summoner_name']


def get_profile_from_db(summoner_name):
    if not summoner_name:
        return None
    item = dynamo.tables['actor_users'].get_item(Key={'summoner_name': summoner_name})
    if item and 'Item' in item:
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

    if 'participants' not in item:
        item['participants'] = {}
    for p in game['info']['participants']:
        item['participants'][p['summonerName']] = {
            'summoner_name': p['summonerName'],
            'assists': p['assists'],
            'kills': p['kills'],
            'deaths': p['deaths'],
            'total_damage': p['totalDamageDealtToChampions'],
            'champion_name': p['championName'],
            'kda': Decimal(str((p['kills'] * 2 + p['assists']) / max(1, p['deaths'])))
        }
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
    first_player = item['player_list'][1][0]
    # print('player', first_player)
    # puuid = dynamo.tables['actor_users'].get_item(Key={'summoner_name': first_player})['Item']['puuid']
    # match_history = get_match_history_from_puuid(puuid)
    try:
        for player in item['player_list']:
            puuid = dynamo.tables['actor_users'].get_item(Key={'summoner_name': player[0]})['Item']['puuid']
            match_history = get_match_history_from_puuid(puuid)
            match_ids = [_['id'] for _ in match_history['data']['matchlist']['matches']]
            # print(match_ids)
            for match_id in match_ids[:5]:
                game = watcher.match.by_id('americas', match_id)
                team100 = [_['summonerName'] for _ in game['info']['participants'] if _['teamId'] == 100]
                team200 = [_['summonerName'] for _ in game['info']['participants'] if _['teamId'] == 200]
                if (set(team100) == set(item['team1']) and set(team200) == set(item['team2'])) or (set(team100) == set(item['team2']) and set(team200) == set(item['team1'])):
                    item['match_id'] = match_id
                    dynamo.tables['actor_game'].put_item(Item=item)
                    update_game_info(game_id, match_id)
                    print('Updated:', game_id)
                    return
    except:
        return None

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
        match_ids = [_['id'] for _ in match_history['data']['matchlist']['matches']]
        history = []
        for match_id in match_ids[:20]:
            game = watcher.match.by_id('americas', match_id)
            game_duration = game['info']['gameDuration']
            game_mode = game['info']['gameMode']
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


def calculate_score(game_id):
    
    item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']
    # calculate for winning team
    winning_team = item['winning_team']
    kda = []
    for idx, summoner_name in enumerate(item[winning_team]):
        item['participants'][summoner_name]['score'] = 1 # default 分数是1
        kda.append(item['participants'][summoner_name]['kda'])
    max_kda_idx = np.argmax(kda)
    if max_kda_idx == item[winning_team+'_actor_idx']: #演员kda最高
        item['participants'][item[winning_team][max_kda_idx]]['score'] = 0
    else: #演员 kda不是最高
        item['participants'][item[winning_team][max_kda_idx]]['score'] = 2 #kda最高 +2
        item['participants'][item[winning_team][int(item[winning_team+'_actor_idx'])]]['score'] = -1 #演员 -1
    
    # calculate for losing team
    losing_team = 'team1' if item['winning_team'] == 'team2' else 'team2'
    kda = []
    for summoner_name in item[losing_team]:
        item['participants'][summoner_name]['score'] = -1 # default 分数是-1
        kda.append(item['participants'][summoner_name]['kda'])
    max_kda_idx = np.argmax(kda)
    
    # count votes
    vote_received = [0] * len(item[losing_team])
    for i in range(len(item[losing_team])):
        vote_received[int(item['votes'][i])] += 1.5 if i == max_kda_idx else 1
        
    zhuojianzaichuang = int(item[losing_team+'_actor_idx']) == np.argmax(vote_received)
    
    # 投对了平民 +0，演员 -3
    if zhuojianzaichuang:
        for idx, summoner_name in enumerate(item[losing_team]):
            item['participants'][summoner_name]['score'] = 0 if idx != item[losing_team+'_actor_idx'] else -3
    else:
        # 【蒙混过关】+3, 【运筹帷幄】+5
        item['participants'][item[losing_team][int(item[losing_team+'_actor_idx'])]]['score'] = 3 if max_kda_idx  != item[losing_team+'_actor_idx'] else 5
    dynamo.tables['actor_game'].put_item(Item=item)
    