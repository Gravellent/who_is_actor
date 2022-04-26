from flask import session, request, redirect, render_template
from controller import get_profile_from_db
from models import dynamo
import random
from decimal import Decimal
import time

def join_game():
    profile = get_profile_from_db(session.get('username', ''))
    if request.method == 'GET':
        return render_template('join.html', profile=profile)
    if request.method == 'POST':
        game_id = request.form['game_id']
        item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})
        if 'Item' not in item:
            return render_template('join.html', not_found=True, profile=profile)
        else:
            item = item['Item']
            if item['game_state'] == 'waiting':
                if session['username'] not in item['player_list'].keys():
                    item['player_list'][session['username']] = {'username': session['username'],
                                                                    'selected_team': 'Random',
                                                                    'total_score': 0}
                    dynamo.tables['actor_game'].put_item(Item=item)
                return redirect(f'games/{game_id}')
            else:
                if session['username'] not in item['player_list'].keys():
                    return render_template('join.html', not_found=True, profile=profile)
                return redirect(f'games/{game_id}')


def create_game():
    game_id = ''.join(str(random.randint(0, 9)) for _ in range(6))  # Generate 6 digit id

    # If ID exists, keep randomly generating game_ids
    while 'Item' in dynamo.tables['actor_game'].get_item(Key={'game_id': game_id}):
        game_id = ''.join(str(random.randint(0, 9)) for _ in range(6))
        

    item = {
        'game_id': game_id,
        'creation_time': Decimal(time.time()),
        'player_list': {},
        'team1': [],
        'team2': [],
        'game_state': 'waiting',
        'team1_actor_idx': 0,
        'team2_actor_idx': 0,
        'votes': [],
        'winning_team': None,
        'next_game_id': None,
        'head_game_id': game_id,
        'admin': session['username']
    }
    
    item['player_list'][session['username']] = {'username': session['username'], 
                                                'selected_team': 'Random',
                                                'total_score': 0}
    dynamo.tables['actor_game'].put_item(Item=item)
    return redirect(f'games/{game_id}')


def next_game(game_id):
    item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']

    # for the first person that clicks next game, generate a new game
    if item['next_game_id'] is None:
        game_id = ''.join(str(random.randint(0, 9)) for _ in range(6))  # Generate 6 digit id

        # If ID exists, keep randomly generating game_ids
        while 'Item' in dynamo.tables['actor_game'].get_item(Key={'game_id': game_id}):
            game_id = ''.join(str(random.randint(0, 9)) for _ in range(6))

        item['next_game_id'] = game_id
        dynamo.tables['actor_game'].put_item(Item=item)

        new_item = {
            'game_id': game_id,
            'creation_time': Decimal(time.time()),
            'player_list': {},
            'team1': [],
            'team2': [],
            'game_state': 'waiting',
            'team1_actor_idx': 0,
            'team2_actor_idx': 0,
            'votes': [],
            'winning_team': None,
            'next_game_id': None,
            'head_game_id': item['head_game_id']

        }
    else:
        game_id = item['next_game_id']
        new_item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']

    new_item['player_list'][session['username']] = {'username': session['username'],
                                                    'selected_team': 'Random',
                                                    'total_score': item['player_list'][session['username']][
                                                        'total_score']}
    dynamo.tables['actor_game'].put_item(Item=new_item)
    return redirect(f'/games/{game_id}')