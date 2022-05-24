from controller import get_profile_from_db, get_leaders
from flask import render_template, session, request, redirect, url_for
import pandas as pd
from common import cache
from controller.champion_selector import *


def champion_selector():
    profile = get_profile_from_db(session.get('username', ''))
    my_position = request.args.get('my_position')
    show_all_champs = request.args.get('show_all_champs', '0')
    show_all_champs = False if show_all_champs == '0' else True
    picked_players = {
        'team_top': request.args.get('team_top', None),
        'team_jungle': request.args.get('team_jungle', None),
        'team_middle': request.args.get('team_middle', None),
        'team_bottom': request.args.get('team_bottom', None),
        'team_support': request.args.get('team_support', None),
        'enemy_top': request.args.get('enemy_top', None),
        'enemy_jungle': request.args.get('enemy_jungle', None),
        'enemy_middle': request.args.get('enemy_middle', None),
        'enemy_bottom': request.args.get('enemy_bottom', None),
        'enemy_support': request.args.get('enemy_support', None),
    }

    champion_list = list(get_most_recent_champion_data().keys())
    positions = [
        ("top", "上路"),
        ("jungle", "打野"),
        ("middle", "中路"),
        ("bottom", "下路"),
        ("support", "辅助"),
    ]
    if my_position not in [_[0] for _ in positions]:
        my_position = None

    current_champion_pool = get_champion_pool(session.get('username'), my_position)
    champion_pool_names = sorted([(id_name_mapping[_], _) for _ in current_champion_pool])
    champs = get_paginated_chmapion_icon(current_champion_pool)
    predicted_win_rate = calculate_win_rate(my_position, current_champion_pool, picked_players)

    return render_template("champion_selector.html", champions=champion_list,
                           positions=positions, profile=profile, my_position=my_position,
                           picked_players=picked_players, champs=champs, champion_pool=champion_pool_names,
                           show_all_champs=show_all_champs, predicted_win_rate=predicted_win_rate)


def add_to_champion_pool_view(position, champion_id):
    add_champion_to_pool(session.get('username'), position, champion_id)
    return redirect(url_for('champion_selector', my_position=position, show_all_champs=1))


def delete_from_champion_pool_view(position, champion_id):
    delete_champion_from_pool(session.get('username'), position, champion_id)
    return redirect(url_for('champion_selector', my_position=position))