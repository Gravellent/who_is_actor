from flask import render_template, session
from controller import get_profile_from_db


def home():
    profile = get_profile_from_db(session.get('username', ''))
    return render_template('home.html', profile=profile)
