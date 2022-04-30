from controller import get_profile_from_db, get_leaders
from flask import render_template, session
import pandas as pd
from common import cache

def champion_selector():
    profile = get_profile_from_db(session.get('username', ''))

    champion_list = pd.read_excel("../static/cid_map.xlsx").Champion
    positions = [
        ("top", "上路"),
        ("jungle", "打野"),
        ("middle", "中路"),
        ("bottom", "下路"),
        ("support", "辅助"),
    ]

    return render_template("champion_selector.html", champions=champion_list, positions=positions)