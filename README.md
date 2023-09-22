# TourneyBot

## Introduction
This bot manages a tournament for the ranked bedwars server.

The majority of the logic is performed within the API, written using Nitro & Cloudflare D1 hosted on Cloudflare Workers.


## Running the fucking thing 
1. Create a python virtual environment, this allows us to use known working versions of modules
```bash
python -m venv ./venv
```

2. Activate the virtual environment
```bash
./venv/Scripts/activate
```

3. Install all dependencies
```bash
pip install -r requirements.txt
```

4. Configure the bot.
There are three main files used for configuration. `constants.json` & `tourney.constants.json` & `.key`

+ `constants.json` - This requires an API key and API URL, get these from ohb00.
+ `tourney.constants.json` - This contains the roles and channels required for running the bot.
+ `.key` - This contains the bot's token.

5. Run the bot
```bash
python ./main.py
```

6. Set up number of players
```discord
-config players 2
```

7. Congratulations! You are now running the bot.