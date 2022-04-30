from common import cache
import views
from flask import Flask

app = Flask(__name__)
app.secret_key = 'Is this some random string?'
config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
}
app.config.from_mapping(config)
cache.init_app(app, config={'CACHE_TYPE': 'simple'})


app.add_url_rule('/', view_func=views.home)
app.add_url_rule('/login', view_func=views.login, methods=['GET', 'POST'])
app.add_url_rule('/logout', view_func=views.logout)
app.add_url_rule('/profile/<summoner_name>', view_func=views.profile)
app.add_url_rule('/leaderboard', view_func=views.leaderboard)
app.add_url_rule('/champion_selector', view_func=views.champion_selector)

app.add_url_rule('/join_game', view_func=views.join_game, methods=['POST', 'GET'])
app.add_url_rule('/create_game', view_func=views.create_game)

app.add_url_rule('/games/<game_id>', view_func=views.game)
app.add_url_rule('/games/<game_id>/start', view_func=views.start_game, methods=['GET', 'POST'])
app.add_url_rule('/games/<game_id>/update', view_func=views.update_game, methods=['POST'])
app.add_url_rule('/games/<game_id>/next_game', view_func=views.next_game, methods=['POST'])
app.add_url_rule('/games/<game_id>/vote', view_func=views.vote, methods=['GET', 'POST'])
app.add_url_rule('/games/<game_id>/end_game', view_func=views.end_game, methods=['GET', 'POST'])
app.add_url_rule('/games/<game_id>/exit_game', view_func=views.exit_game, methods=['POST'])


if __name__ == '__main__':
    app.run()
