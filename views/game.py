from flask import session, render_template, request, redirect
from models import dynamo
from controller import get_profile_from_db, populate_game_data_from_history, add_game_to_profile, calculate_losing_score, update_total_score, update_elo
import random


def game(game_id):
    profile = get_profile_from_db(session.get('username', ''))
    if not profile:
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
            (session['username'] in item['team2'] and item['team2'][int(item['team2_actor_idx'])] == session
                ['username']):
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


def start_game(game_id):
    item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']
    if request.method == 'POST' and item['game_state'] == 'waiting' and len(item['player_list']) > 1:
        # 只有第一名才能开始游戏
        if item['player_list'][session['username']]['total_score'] != \
                sorted(item['player_list'].items(), key=lambda kv: kv[1]['total_score'], reverse=True)[0][1][
                    'total_score']:
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


def update_game(game_id):
    if populate_game_data_from_history(game_id):
        item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']
        item['game_state'] = 'voting'
        dynamo.tables['actor_game'].put_item(Item=item)
    return redirect(f'/games/{game_id}')


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
            return redirect(f'/games/{game_id}/end_game')
    request.form  # For some reason this fixes the 405 error..
    return redirect(f'/games/{game_id}')

def kick(game_id, summoner_name):
    item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']
    item['player_list'].pop(summoner_name, None)
    dynamo.tables['actor_game'].put_item(Item=item)
    return redirect(f'/games/{game_id}')


def end_game(game_id):
    item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']
    calculate_losing_score(game_id)
    update_total_score(game_id)
    if len(item['player_list']) == 8:
        update_elo(game_id)
        for username in item['player_list']:
            profile = get_profile_from_db(username)
            add_game_to_profile(profile, item)
    item['game_state'] = 'ended'
    
    dynamo.tables['actor_game'].put_item(Item=item)
    return redirect(f'/games/{game_id}')


def exit_game(game_id):
    item = dynamo.tables['actor_game'].get_item(Key={'game_id': game_id})['Item']
    profile = get_profile_from_db(session.get('username', ''))
    return render_template('exit.html', game=item,
                           profile=profile)