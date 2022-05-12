from controller import get_profile_from_db, get_leaders
from flask import render_template, session, request
import pandas as pd
from common import cache
from controller.champion_selector import get_champion_stat

def champion_selector():
    profile = get_profile_from_db(session.get('username', ''))
    my_position = request.args.get('my_position')
    picked_players = {
        'ally_top': request.args.get('ally_top', None),
        'ally_jungle': request.args.get('ally_jungle', None),
        'ally_middle': request.args.get('ally_middle', None),
        'ally_bottom': request.args.get('ally_bottom', None),
        'ally_support': request.args.get('ally_support', None),
        'enemy_top': request.args.get('enemy_top', None),
        'enemy_jungle': request.args.get('enemy_jungle', None),
        'enemy_middle': request.args.get('enemy_middle', None),
        'enemy_bottom': request.args.get('enemy_bottom', None),
        'enemy_support': request.args.get('enemy_support', None),
    }

    champion_list = pd.read_csv("static/cid_map.csv").Champion
    positions = [
        ("top", "上路"),
        ("jungle", "打野"),
        ("middle", "中路"),
        ("bottom", "下路"),
        ("support", "辅助"),
    ]
    if my_position not in [_[0] for _ in positions]:
        my_position = None

    stat = get_champion_stat('Ahri', my_position)
    # print(stat)


    return render_template("champion_selector.html", champions=champion_list,
                           positions=positions, profile=profile, my_position=my_position, stat=stat,
                           picked_players=picked_players)