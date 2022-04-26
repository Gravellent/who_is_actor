from controller import get_profile_from_db, get_leaders
from flask import render_template, session
from common import cache

def leaderboard():
    profile = get_profile_from_db(session.get('username', ''))

    @cache.cached(timeout=50, key_prefix='leaders')
    def get_leader():
        return get_leaders()

    leaders = get_leader()
    return render_template("leaderboard.html", profile=profile, leaders=leaders)