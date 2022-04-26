from models import dynamo
from decimal import Decimal
import numpy as np

def calculate_winning_score(game_id):
    item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']
    winning_team = item['winning_team']
    kda = []
    item['chenghao'] = []

    for idx, summoner_name in enumerate(item[winning_team]):
        item['player_list'][summoner_name]['score'] = 2  # default 分数是2
        item['player_list'][summoner_name]['result'] = 'p_win'
        kda.append(item['player_list'][summoner_name]['kda'])
    max_kda_idx = np.argmax(kda).item()
    item['winning_team_max_kda_idx'] = max_kda_idx
    if max_kda_idx == item[winning_team + '_actor_idx']:  # 演员kda最高
        item['player_list'][item[winning_team][max_kda_idx]]['score'] = -1
        item['player_list'][item[winning_team][max_kda_idx]]['result'] = 'y_win_gxgz'
        # item['chenghao'].append('gxgz')
    else:  # 演员 kda不是最高
        item['player_list'][item[winning_team][max_kda_idx]]['score'] = 4
        item['player_list'][item[winning_team][max_kda_idx]]['result'] = 'p_win_max'
        item['player_list'][item[winning_team][int(item[winning_team + '_actor_idx'])]]['score'] = -3
        item['player_list'][item[winning_team][int(item[winning_team + '_actor_idx'])]]['result'] = 'y_win'
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

    zhuojianzaichuang = int(item[losing_team + '_actor_idx']) == np.argmax(vote_received)

    # 投对了平民 +0，演员 -3
    if zhuojianzaichuang:  # 捉奸在床
        for idx, summoner_name in enumerate(item[losing_team]):
            if idx != item[losing_team + '_actor_idx']:
                item['player_list'][summoner_name]['score'] = 0
                item['player_list'][summoner_name]['result'] = 'p_lose_zjzc'
            else:
                item['player_list'][summoner_name]['score'] = -5
                item['player_list'][summoner_name]['result'] = 'y_lose_zjzc'
        item['chenghao'].append('zjzc')
    elif max_kda_idx != int(item[losing_team + '_actor_idx']):  # 蒙混过关
        for idx, summoner_name in enumerate(item[losing_team]):
            if idx != item[losing_team + '_actor_idx']:
                item['player_list'][summoner_name]['score'] = Decimal(-2.5)
                item['player_list'][summoner_name]['result'] = 'p_lose_mhgg'
            else:
                item['player_list'][summoner_name]['score'] = Decimal(4.5)
                item['player_list'][summoner_name]['result'] = 'y_lose_mhgg'
        item['chenghao'].append('mhgg')
    else:  # 运筹帷幄
        for idx, summoner_name in enumerate(item[losing_team]):
            if idx != item[losing_team + '_actor_idx']:
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
