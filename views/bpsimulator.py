from controller import get_profile_from_db, get_leaders
from flask import render_template, session, request, redirect, url_for
import pandas as pd
from common import cache
from controller.bpsimulator import *

def bpsimulator():
    profile = get_profile_from_db(session.get('username', ''))
    picked_players = {
        'left_top': request.args.get('left_top', None),
        'left_jungle': request.args.get('left_jungle', None),
        'left_middle': request.args.get('left_middle', None),
        'left_bottom': request.args.get('left_bottom', None),
        'left_support': request.args.get('left_support', None),
        'right_top': request.args.get('right_top', None),
        'right_jungle': request.args.get('right_jungle', None),
        'right_middle': request.args.get('right_middle', None),
        'right_bottom': request.args.get('right_bottom', None),
        'right_support': request.args.get('right_support', None),
    }
    champion_list = list(get_most_recent_champion_data().keys())
    positions = [
        ("top", "上路"),
        ("jungle", "打野"),
        ("middle", "中路"),
        ("bottom", "下路"),
        ("support", "辅助"),
    ]

    win_rate = calculate_win_rate(picked_players)
    left_team = []
    right_team = []
    left_total = 0
    right_total = 0
    for i in win_rate:
        if i["position"][:1] == 'l':
            left_team.append(i["winrate"])
            left_total += i["winrate"]
        else:
            right_team.append(i["winrate"])
            right_total += i["winrate"]

    if left_total != 0 or right_total != 0:
        left_winrate = (left_total / 5) / (left_total / 5 + right_total / 5) * 100
        right_winrate = (right_total / 5) / (left_total / 5 + right_total / 5) * 100
    else:
        left_winrate = 0
        right_winrate = 0

    return render_template("bpsimulator.html", champions=champion_list,
                           positions=positions, profile=profile,
                           picked_players=picked_players, win_rate=win_rate,
                           left_team=left_team, right_team=right_team,
                           left_winrate=left_winrate,right_winrate=right_winrate)