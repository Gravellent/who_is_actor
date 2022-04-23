from flask import Flask, redirect
from flask import render_template
from flask import request, url_for, session
from flask_caching import Cache

import sys
import time
import random
from decimal import Decimal

from models import dynamo
from controller import *
from elo import *

app = Flask(__name__)

app.secret_key = 'Is this some random string?'
config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
}
app.config.from_mapping(config)
cache = Cache(app)


# TODO:
# 3. Add password for log in
# 4. Store match result (requires KDA calculation)
# 5. Leaderboard: Needs to store each match result
# Only creator of the game can start game
# Vote can be part of the participants dict in db, also applies to team1 and team2. participants can have
# more fields
# Show rank in game lobby
# English version
# Some caching: Profile crawl, game crawl can have an min update time
# A larger instance and load balance if more users use this
# Some way to invalidate games if they are in waiting/ started for too long
# Game id needs to be more scalable (Maybe date + id)
# Clean up unused game ids
# Some protective measurement for DDOS
# Automatically determine winner and loser
# Add CSS
# Need to store match history more permanently


# Maybe:
# 1. Allow user to select team1 or team2

@app.route('/')
def home():
    profile = get_profile_from_db(session.get('username', ''))
    return render_template('home.html', username=session.get('username'), profile=profile)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    try:
        # Some name are capitalized in some ways so it has to be corrected here
        summoner_name = import_profile_to_db(request.form['username'])
    except:
        print('Username not allowed')
        return render_template('login.html', message="未能找到该召唤师信息!")
    session['username'] = summoner_name
    return redirect(url_for('home'))


# @app.route('/log_in', methods=['GET', 'POST', 'PUT'])
# def login_handler():


@app.route('/logout', methods=['GET'])
def logout():
    if 'username' in session:
        session.pop('username')
    return redirect(url_for('home'))


@app.route('/join_game', methods=['POST', 'GET'])
def join_game():
    profile = get_profile_from_db(session.get('username', ''))
    if request.method == 'GET':
        return render_template('join.html', username=session.get('username'), profile=profile)
    if request.method == 'POST':
        game_id = request.form['game_id']
        item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})
        if 'Item' not in item:
            return render_template('join.html', not_found=True, username=session.get('username'), profile=profile)
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
                    return render_template('join.html', not_found=True, username=session.get('username'), profile=profile)
                return redirect(f'games/{game_id}')


@app.route('/create_game', methods=['GET'])
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
        'head_game_id': game_id
    }
    
    item['player_list'][session['username']] = {'username': session['username'], 
                                                'selected_team': 'Random',
                                                'total_score': 0}
    dynamo.tables['actor_game'].put_item(Item=item)
    return redirect(f'games/{game_id}')

@app.route('/games/<game_id>/next_game', methods=['POST'])
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
                                                    'total_score': item['player_list'][session['username']]['total_score']}
    dynamo.tables['actor_game'].put_item(Item=new_item)
    return redirect(f'/games/{game_id}')
        

@app.route('/games/<game_id>', methods=['GET'])
def games(game_id):
    profile = get_profile_from_db(session.get('username', ''))
    if 'username' not in session:
        return render_template('login.html', message="请先登录!")
    item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']
    game_state = item['game_state']
    player_list = list(item['player_list'].keys())
    dynamo.tables['actor_game'].put_item(Item=item)

    # Check which team the logged in user belongs to and whether user has voted
    team_belonging = None
    has_voted = None
    if session['username'] in item['team1']:
        team_belonging = 'team1'
        if len(item['votes']) > 0:
            has_voted = item['votes'][item['team1'].index(session['username'])]
    if session['username'] in item['team2']:
        team_belonging = 'team2'
        if len(item['votes']) > 0:
            has_voted = item['votes'][item['team2'].index(session['username'])]

    # Check if the user is an actor
    if (session['username'] in item['team1'] and item['team1'][int(item['team1_actor_idx'])] == session['username']) or \
            (session['username'] in item['team2'] and item['team2'][int(item['team2_actor_idx'])] == session['username']):
        role = 'actor'
    else:
        role = 'non-actor'
    

    return render_template('game.html', game_id=game_id, state=game_state,
                           team1=item['team1'],
                           team2=item['team2'],
                           role=role,
                           team_belonging=team_belonging,
                           winning_team=item['winning_team'],
                           team1_actor_idx=int(item['team1_actor_idx']),
                           team2_actor_idx=int(item['team2_actor_idx']),
                           votes=item['votes'],
                           has_voted=int(has_voted) if has_voted is not None else has_voted,
                           username=session.get('username'),
                           profile=profile,
                           game=item)


@app.route('/profile/<summoner_name>', methods=['GET'])
def get_profile(summoner_name):
    profile = get_profile_from_db(session.get('username', ''))
    update_profile_match_history(profile)
    return render_template("profile.html", profile=profile, username=session.get('username', ''))

@app.route('/leaderboard', methods=['GET'])
@cache.cached(timeout=30)
def get_leaderboard():
    profile = get_profile_from_db(session.get('username', ''))
    leaders = get_leaders()
    return render_template("leaderboard.html", profile=profile, username=session.get('username', ''), leaders=leaders)

@app.route('/games/<game_id>/start', methods=['GET', 'POST'])
def start_game(game_id):
    item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']
    if request.method == 'POST' and item['game_state'] == 'waiting' and len(item['player_list']) > 1:
        # 只有第一名才能开始游戏
        if item['player_list'][session['username']]['total_score'] != sorted(item['player_list'].items(), key=lambda kv: kv[1]['total_score'], reverse=True)[0][1]['total_score']:
            return redirect(f'/games/{game_id}')
        item['game_state'] = 'started'
        player_list = list(item['player_list'].keys())
        assigned_team1 = random.sample(player_list, len(player_list) // 2)
        for p in item['player_list'].keys():
            if p in assigned_team1:
                item['player_list'][p]['assigned_team'] = 'team1'
                item['team1'].append(p)
            else:
                item['player_list'][p]['assigned_team'] = 'team2'
                item['team2'].append(p)
        
        item['team1_actor_idx'] = random.randint(0, len(item['team1']) - 1)
        item['team2_actor_idx'] = random.randint(0, len(item['team2']) - 1)
        dynamo.tables['actor_game'].put_item(Item=item)
    return redirect(f'/games/{game_id}')

@app.route('/games/<game_id>/update', methods=['POST'])
def update_game(game_id):
    if populate_game_data_from_history(game_id):
        item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']
        item['game_state'] = 'voting'
        dynamo.tables['actor_game'].put_item(Item=item)
    return redirect(f'/games/{game_id}')


@app.route('/games/<game_id>/vote', methods=['GET', 'POST'])
def vote(game_id):
    item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']
    # when a vote comes in, update vote field in db
    if request.method == 'POST' and item['game_state'] == 'voting':
        
        losing_team = 'team1'
        if item['winning_team'] == 'team1':
            losing_team = 'team2'
        user_index = item[losing_team].index(session.get('username'))
        item['votes'][user_index] = request.form['vote']
        dynamo.tables['actor_game'].put_item(Item=item)
        
        # if everyone has voted, go to end game
        if (sum(v is None for v in item['votes']) == 0): 
            item['game_state'] = 'ended'
            dynamo.tables['actor_game'].put_item(Item=item)
            calculate_losing_score(game_id)
            update_total_score(game_id)
            if len(item['player_list']) == 8:
                update_elo(game_id)
            return redirect(f'/games/{game_id}/end_game')
    request.form # For some reason this fixes the 405 error..
    return redirect(f'/games/{game_id}')

@app.route('/games/<game_id>/end_game', methods=['GET', 'POST'])
def end_game(game_id):
    item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']
    if request.method == 'POST' and item['game_state'] == 'voting':
        item['game_state'] = 'ended'
        dynamo.tables['actor_game'].put_item(Item=item)
    return redirect(f'/games/{game_id}')

@app.route('/games/<game_id>/exit_game', methods=['POST'])
def exit_game(game_id):
    item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']
    profile = get_profile_from_db(session.get('username', ''))
    return render_template('exit.html', game=item,
                           profile=profile,
                           username=session.get('username'))

if __name__ == '__main__':
    app.run()
