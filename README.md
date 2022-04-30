# 谁是演员

The server code for the league spin-off game 谁是演员

### Running locally
Server is a simple flask server using basic MVC structure. 
Run `pip install -r requirements.txt` to install all dependencies. Run `flask run` to run server at 5000 port.
The current version requires a RIOT key to fetch the game information. The key can be obtained via 
https://developer.riotgames.com/

Once you have the API key, export to env via `export RIOT_API_KEY=RGAPI-xxxxxxxxx` before running server.

### Database

The server uses a dynamo backend, so you need to run `aws configure` to connect Dyanmo first. 


