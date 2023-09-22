import asyncio
import aiohttp
import logging
import discord
import discord.ext
from discord.ext import commands
from cogs.tourney import *
from api import API

intents = discord.Intents.all()
intents.presences = False

prefix = "-"
key = None
bot = commands.Bot(command_prefix=prefix, intents=intents)

# Commands
commands_dir = './cogs'
commands_dir_p = "cogs"

API_URL = "https://play.bryces.io"
API_AUTH = "UG9zdGFnZTktU3lub3BzZXM5LUJyb3diZWF0NS1SZWNvaWw3"

async def init():
    async with aiohttp.ClientSession(API_URL, headers={"Authorization": API_AUTH}) as session:

        bot.api = API(session)
        bot.prefix = prefix

        async with bot:

            discord.utils.setup_logging(level=logging.INFO, root=False)

            await bot.load_extension('cogs.tourney')
            await bot.login(key)
            await bot.connect()

with open('.key', 'r') as f:
    key = f.read()

asyncio.run(init())



