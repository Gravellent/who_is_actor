from controller import get_profile_from_db, get_leaders
from flask import render_template, session, request
import pandas as pd
from common import cache

def champion_selector():
    profile = get_profile_from_db(session.get('username', ''))
    my_position = request.args.get('my_position')

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

    return render_template("champion_selector.html", champions=champion_list, positions=positions, profile=profile, my_position=my_position)