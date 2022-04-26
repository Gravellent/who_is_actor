from models import dynamo
from boto3.dynamodb.conditions import Attr

def get_leaders():
    print("Getting leaders..")
    users = dynamo.tables['actor_users'].scan(
        FilterExpression=Attr('elo').gt(0),
        ProjectionExpression='summoner_name, profile_icon, elo, skin_received, skin_gifted'
    )
    leaders = sorted(users['Items'], key=lambda x: x['elo'])[::-1][:50]
    for i in range(len(leaders)):
        if 'skin_received' not in leaders[i] or not leaders[i]['skin_received']:
            leaders[i]['skin_received'] = '-'
        if 'skin_gifted' not in leaders[i] or not leaders[i]['skin_gifted']:
            leaders[i]['skin_gifted'] = '-'
    return leaders