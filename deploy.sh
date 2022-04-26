mkdir -p /mnt/services
cd /mnt/services
repo="who_is_actor"
cd "$repo"
git checkout main
git pull

#apt update
apt -y upgrade
apt install -y python3-pip
pip3 install -r requirements.txt

echo Please input your RIOT API KEY:
read riotkey
export RIOT_API_KEY=$riotkey

kill $(ps aux | grep "python3 -m flask run -p 80 -h 0.0.0.0" | awk '{print $2}')
nohup python3 -m flask run -p 80 -h 0.0.0.0 &

