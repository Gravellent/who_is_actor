import requests

def get_profile_from_name(summoner_name):
    return requests.get(
        f'https://riot.iesdev.com/graphql?query=query%20LeagueProfile%28%24summoner_name%3AString%2C%24summoner_id%3AString%2C%24account_id%3AString%2C%24region%3ARegion%21%2C%24puuid%3AString%29%7BleagueProfile%28summoner_name%3A%24summoner_name%2Csummoner_id%3A%24summoner_id%2Caccount_id%3A%24account_id%2Cregion%3A%24region%2Cpuuid%3A%24puuid%29%7Bid%20accountId%20puuid%20summonerId%20summonerName%20summonerLevel%20profileIconId%20updatedAt%20latestRanks%7Bqueue%20tier%20rank%20wins%20losses%20leaguePoints%20insertedAt%7D%7D%7D&variables=%7B%22summoner_name%22%3A%22{summoner_name}%22%2C%22region%22%3A%22NA1%22%7D'
    ).json()

def get_match_history_from_puuid(puuid):
    return requests.get(
    'https://riot.iesdev.com/graphql?query=query%20LeagueMatchlist($region:Region!,$puuid:ID!){matchlist(region:$region,puuid:$puuid){matches{id%20playerMatch{id%20playerMatchStats{lp}}}}}&variables={%22region%22:%22NA1%22,%22puuid%22:%22' + puuid +'%22}').json()