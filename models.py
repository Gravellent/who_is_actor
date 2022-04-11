from flask import Flask
from flask_dynamo import Dynamo

app = Flask(__name__)
app.config['DYNAMO_TABLES'] = [
    dict(
         TableName='actor_game',
         KeySchema=[dict(AttributeName='game_id', KeyType='HASH')],
         AttributeDefinitions=[dict(AttributeName='game_id', AttributeType='S')],
         ProvisionedThroughput=dict(ReadCapacityUnits=5, WriteCapacityUnits=5)
    ),
    dict(
        TableName='actor_users',
        KeySchema=[
            dict(AttributeName='summoner_name', KeyType='HASH'),
        ],
        AttributeDefinitions=[
            dict(AttributeName='summoner_name', AttributeType='S'),
        ],
        ProvisionedThroughput=dict(ReadCapacityUnits=5, WriteCapacityUnits=5)
    )
]


dynamo = Dynamo(app)

with app.app_context():
    dynamo.create_all()
