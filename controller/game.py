import datetime
from models import dynamo
from .blitz import get_match_history_from_puuid
from .riot import watcher, update_game_info
from .score import calculate_winning_score



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
                if (set(team100) == set(item['team1']) and set(team200) == set(item['team2'])) or \
                        (set(team100) == set(item['team2']) and set(team200) == set(item['team1'])):
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