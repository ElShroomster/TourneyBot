import asyncio
import aiohttp
import logging
import json
import discord
import discord.ext
from discord.ext import commands
from cogs.tourney import *
from api import API

intents = discord.Intents.all()
intents.presences = False

key = None
constants = None

prefix = "-"
bot = commands.Bot(command_prefix=prefix, intents=intents)

bot.help_command = None

with open('.key', 'r') as f:
    key = f.read()

with open('constants.json', 'r') as f:
    data = f.read()
    constants = json.loads(data)

API_URL = constants["API_URL"]
API_KEY = constants["API_KEY"]

async def init():

    async with aiohttp.ClientSession(API_URL, headers={"Authorization": API_KEY}) as session:

        bot.api = API(session)
        bot.prefix = prefix

        async with bot:

            discord.utils.setup_logging(level=logging.INFO, root=False)

            await bot.load_extension('cogs.tourney')
            await bot.login(key)
            await bot.connect()

asyncio.run(init())