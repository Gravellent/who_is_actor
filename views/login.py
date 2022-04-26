from flask import session, render_template, request, redirect, url_for
from controller import get_profile_from_db, import_profile_to_db


def login():
    profile = get_profile_from_db(session.get('username', ''))
    if request.method == 'GET':
        return render_template('login.html', profile=profile)

    try:
        # Some name are capitalized in some ways so it has to be corrected here
        summoner_name = import_profile_to_db(request.form['username'])
    except:
        print('Username not allowed')
        return render_template('login.html', message="未能找到该召唤师信息!", profile=profile)
    session['username'] = summoner_name
    return redirect(url_for('home'))


def logout():
    if 'username' in session:
        session.pop('username')
    return redirect(url_for('home'))