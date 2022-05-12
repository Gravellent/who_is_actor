from models import dynamo
from common import cache


@cache.cached(timeout=50)
def get_champion_stat(champion, position):
    item = dynamo.tables['lol_analytics_table'].get_item(Key={"champion": champion})
    if 'Item' not in item:
        return None
    return item['Item'].get(position, None)

