import boto3
import requests

from models import dynamo


def import_profile_to_db(summoner_name):
    profile = get_profile_from_name(summoner_name)['data']
    if profile:
        profile = profile['leagueProfile']
        item = {
            'summoner_name': profile['summonerName'],
            'latest_ranks': profile['latestRanks'],
            'profile_icon': profile['profileIconId'],
            'puuid': profile['puuid'],
            'summoner_level': profile['summonerLevel'],
            'summoner_id': profile['summonerId'],
            'account_id': profile['accountId'],
        }
        dynamo.tables['actor_users'].put_item(Item=item)


def get_profile_from_name(summoner_name):
        return requests.get(
            f'https://riot.iesdev.com/graphql?query=query%20LeagueProfile%28%24summoner_name%3AString%2C%24summoner_id%3AString%2C%24account_id%3AString%2C%24region%3ARegion%21%2C%24puuid%3AString%29%7BleagueProfile%28summoner_name%3A%24summoner_name%2Csummoner_id%3A%24summoner_id%2Caccount_id%3A%24account_id%2Cregion%3A%24region%2Cpuuid%3A%24puuid%29%7Bid%20accountId%20puuid%20summonerId%20summonerName%20summonerLevel%20profileIconId%20updatedAt%20latestRanks%7Bqueue%20tier%20rank%20wins%20losses%20leaguePoints%20insertedAt%7D%7D%7D&variables=%7B%22summoner_name%22%3A%22{summoner_name}%22%2C%22region%22%3A%22NA1%22%7D'
        ).json()


def get_profile_from_db(summoner_name):
    if not summoner_name:
        return None
    item = dynamo.tables['actor_users'].get_item(Key={'summoner_name': summoner_name})
    if item:
        return item['Item']
    else:
        return None


def update_game_info(summoner_name):

