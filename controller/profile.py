from models import dynamo
from .blitz import get_profile_from_name
import datetime
from .blitz import get_match_history_from_puuid
from .riot import watcher
from decimal import Decimal


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



def import_profile_to_db(summoner_name):
    profile = get_profile_from_name(summoner_name)['data']['leagueProfile']
    item = dynamo.tables['actor_users'].get_item(Key={'summoner_name': profile['summonerName']}).get('Item', '')
    if item:
        if 'elo' not in item:
            item['elo'] = 1200
            dynamo.tables['actor_users'].put_item(Item=item)
    else:
        item = {
            'summoner_name': profile['summonerName'],
            'latest_ranks': profile['latestRanks'],
            'profile_icon': profile['profileIconId'],
            'puuid': profile['puuid'],
            'summoner_level': profile['summonerLevel'],
            'summoner_id': profile['summonerId'],
            'account_id': profile['accountId'],
            'elo': 1200,
        }
        dynamo.tables['actor_users'].put_item(Item=item)
    return item['summoner_name']


def get_profile_from_db(summoner_name):
    if not summoner_name:
        return None
    return dynamo.tables['actor_users'].get_item(Key={'summoner_name': summoner_name})['Item']