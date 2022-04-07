from flask import Flask
from flask import render_template
from flask import request

import time
import random
from decimal import Decimal

from models import dynamo

app = Flask(__name__)

# TODO:
# 1. Voting system
# 2. Can pick team 1 or team 2
# 3. Connect with Riot backend to get user's information
# 4. Get a domain name and set up A record
# 5. Set up a database to permanent store result
# 6. Set up to allow multiple game on the same time
# 7. Run in background
# 8. Get nicknames from somewhere else so it's more unique
# 9. Set up a login system so users can log into the system and record their results

all_nicknames = ['老鼠', '狮子', '大象', '狐狸', '哈士奇', '猩猩', '海豚', '鲸鱼', '鹦鹉', '猫咪']
nicknames = ['老鼠', '狮子', '大象', '狐狸', '哈士奇', '猩猩', '海豚', '鲸鱼', '鹦鹉', '猫咪']

player_list, team1, team2 = [], [], []
team1_actor_idx, team2_actor_idx = None, None
global game_state
game_state = 'waiting'


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register_completion', methods=['POST'])
def register_completion():
    player = request.form['player']
    team = request.form['team']
    if len(nicknames) == 0:
        success = False
        return render_template('register_completion.html', success=success)
    else:
        success = True
    random.shuffle(nicknames)
    nickname = nicknames.pop()
    player_list.append((player, nickname, team))
    return render_template('register_completion.html', success=success, nickname=nickname, player=player)


@app.route('/create', methods=['POST', 'GET'])
def create():
    return render_template('create.html')

@app.route('/create_game', methods=['GET'])
def create_game():
    game_id = ''.join(str(random.randint(0, 9)) for _ in range(6))  # Generate 6 digit id
    dynamo.tables['actor_game'].put_item(Item={
        'game_id': game_id,
        'creation_time': Decimal(time.time()),
    })
    return ('', 200)


@app.route('/game', methods=['POST', 'GET'])
def game():
    global game_state
    global player_list
    global nicknames
    global team1
    global team2
    global team1_actor_idx
    global team2_actor_idx

    if request.args.get('start_game') == 'started' and len(player_list) > 1 and game_state == 'waiting':
        game_state = 'started'
        random.shuffle(player_list)
        for i in range(len(player_list) // 2):
            team1.append(player_list.pop())
        team2 = [_ for _ in player_list]
        team1_actor_idx = random.randint(0, len(team1)-1)
        team2_actor_idx = random.randint(0, len(team2)-1)
    if request.args.get('start_game') == 'ended' and game_state == 'started':
        game_state = 'ended'
    if request.args.get('start_game') == 'waiting' and game_state == 'ended':
        game_state = 'waiting'
        nicknames = all_nicknames.copy()
        team1, team2, player_list = [], [], []
        team1_actor_idx, team2_actor_idx = None, None
    return render_template('game.html', state=game_state, players=player_list, team1=team1, team2=team2,
                           team1_actor_idx=team1_actor_idx, team2_actor_idx=team2_actor_idx)


if __name__ == '__main__':
    app.run()
