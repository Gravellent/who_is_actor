from flask import render_template, session
from controller import get_profile_from_db, update_profile_match_history


def profile(summoner_name):
    profile = get_profile_from_db(session.get('username', ''))
    update_profile_match_history(profile)
    return render_template("profile.html", profile=profile)