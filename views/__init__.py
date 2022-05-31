from .home import *
from .login import *
from .join_game import *
from .game import *
from .profile import *
from .leaderboard import leaderboard
from .champion_selector import *
from .bpsimulator import *


def riot_verificaiton():
    return render_template('riot.txt')
