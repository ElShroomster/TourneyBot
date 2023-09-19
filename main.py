import asyncio
import os

import discord
from cogs.tourney import *

import discord.ext
import random
from datetime import datetime
import json

import datetime
from discord.ui import View, Button
from discord.ext import commands

intents = discord.Intents.all()
intents.presences = False

bot = commands.Bot(command_prefix="-", intents=intents)

constants = None
with open("constants.json", "r", encoding="utf-8") as rt:
    rt.seek(0)
    constants = json.load(rt)

# -- Constants

SERVER_ID = constants["SERVER_ID"]
VOTE_CHANNEL_PUGS = constants["VOTE_CHANNEL_PUGS"]
PUGS_ROLE = constants["PUGS_ROLE"]
PUGS_MANAGER_ROLE = constants["PUGS_MANAGER_ROLE"]
PUGS_CONFIRM = constants["PUGS_CONFIRM"]
STRIKE_REQUEST_CHANNEL = constants["STRIKE_REQUEST_CHANNEL"]
CONFIRM_STRIKE_CHANNEL = constants["CONFIRM_STRIKE_CHANNEL"]
PUGS_ANNOUNCEMENTS = constants["PUGS_ANNOUNCEMENTS"]
PUGS_TRIAL_ROLE = constants["PUGS_TRIAL_ROLE"]


# -- Functions

# Commands
commands_dir = './cogs'
commands_dir_p = "cogs"

# -- Commands
#@bot.command()
#async def help(ctx):
#    await context.send("Custom help command")

@commands.has_role(PUGS_MANAGER_ROLE)
@bot.command(name="pugstrial", description="Give or remove Pugs trial from someone")
async def pugstrial(ctx, setting: str, user: discord.Member):
    server = bot.get_guild(SERVER_ID)
    pugsannc = server.get_channel(PUGS_ANNOUNCEMENTS)
    if setting.lower() == "add":
        PugsTrialRole = server.get_role(PUGS_TRIAL_ROLE)
        PugsRole = server.get_role(PUGS_ROLE)
        if not PugsTrialRole in user.roles:
            await user.add_roles(PugsTrialRole)
            Embed_Channel = discord.Embed(title="Ranked Bedwars PUGs",
                                          description=f"You have successfully given <@{user.id}> PUGs Trial!",
                                          color=0xe91e63)

            await ctx.send(content=user.mention, embed=Embed_Channel)

            Embed_PUGS = discord.Embed(title="Ranked Bedwars PUGs",
                                       description=f"Congratulations {user.mention} for receiving `PUGs Trial`!",
                                       color=0x992d22)
            await pugsannc.send(content=user.mention, embed=Embed_PUGS)
        if not PugsRole in user.roles:
            await user.add_roles(PugsRole)
    elif setting.lower() == "remove":
        PugsRole = server.get_role(PUGS_ROLE)
        PugsTrialRole = server.get_role(PUGS_TRIAL_ROLE)
        if PugsTrialRole in user.roles:
            await user.remove_roles(PugsTrialRole)
            Embed_Channel = discord.Embed(title="Ranked Bedwars PUGs",
                                          description=f"Succesfully removed PUGs Trial from <@{user.id}>",
                                          color=0xe91e63)

            await ctx.send(content=user.mention, embed=Embed_Channel)
    else:

        Embed_Channel = discord.Embed(title="Ranked Bedwars",
                                      description=f"Accepted Arguements: add | remove (usage: .pugstrial <add/remove> <user>)"
                                      )

        await ctx.send(content=user.mention, embed=Embed_Channel)


@bot.command(name="pugsvote", description="Request a pugs vote", aliases=["pv", "vote"])
async def pugsvote(ctx, query: str, user: discord.Member = None):
    server = bot.get_guild(SERVER_ID)
    pugsrole = server.get_role(PUGS_ROLE)
    pugsmanager = server.get_role(PUGS_MANAGER_ROLE)
    pugsvoting = server.get_channel(VOTE_CHANNEL_PUGS)
    pugsconfirmation = server.get_channel(PUGS_CONFIRM)
    with open("DataVote.json", "r", encoding="utf-8") as rt:
        rt.seek(0)
        DataVote = json.load(rt)

    if query.lower() == "request":

        if str(ctx.message.author.id) in DataVote:
            if ":" not in DataVote[str(ctx.message.author.id)]:
                QrVote = DataVote[str(ctx.message.author.id)]
                if QrVote == "0" or QrVote == "1":
                    DataVote[str(ctx.message.author.id)] = "3"
                    em1 = discord.Embed(
                        title=ctx.message.author.display_name,
                        description=f"PENDING",
                        color=discord.Color.from_rgb(255, 255, 255),
                    )
                    em1.set_author(name="RBW Pugs")
                    messagePugs = await pugsconfirmation.send(
                        content=ctx.message.author.id, embed=em1
                    )
                    await messagePugs.add_reaction("✅")
                    await messagePugs.add_reaction("❌")
                    em2 = discord.Embed(
                        title="RBW Pugs",
                        description=f"Succesfully requested a vote.",
                        color=discord.Color.from_rgb(255, 255, 255),
                    )
                    await ctx.reply(embed=em2, ephemeral=True)
                elif QrVote == "3":
                    em2 = discord.Embed(
                        title="RBW Pugs",
                        description=f"You have already requested a vote that is yet to be reviewed.",
                        color=discord.Color.from_rgb(255, 255, 255),
                    )
                    await ctx.reply(embed=em2, ephemeral=True)
                with open("DataVote.json", "w") as wwr:
                    json.dump(DataVote, wwr)
            else:
                DataVote[str(ctx.message.id)] = "0"
                with open("DataVote.json", "w") as wwr:
                    json.dump(DataVote, wwr)

                em2 = discord.Embed(
                    title="RBW Pugs",
                    description=f"You already have a vote!",
                    color=discord.Color.from_rgb(255, 255, 255),
                )
                await ctx.reply(embed=em2, ephemeral=True)
        else:

            DataVote[str(ctx.message.author.id)] = "0"
            with open("DataVote.json", "w") as wwr:
                json.dump(DataVote, wwr)

            em2 = discord.Embed(
                title="RBW Pugs",
                description=f"You have been added to the database. Please run the command again.",
                color=discord.Color.from_rgb(255, 255, 255),
            )
            await ctx.reply(embed=em2, ephemeral=True)
    elif query.lower() == "give":
        if not pugsmanager in user.roles:
            em2 = discord.Embed(
                title="RBW Pugs",
                description=f"You have to have `PUGS MANAGER` in order to give other people votes.",
                color=discord.Color.from_rgb(255, 255, 255),
            )
            await ctx.reply(embed=em2, ephemeral=True)
            return
        PugsVoteChannel = server.get_channel(VOTE_CHANNEL_PUGS)
        userVote = user
        EmbedVote = discord.Embed(title="RBW PUGs", description=userVote.display_name,
                                  color=discord.Color.from_rgb(43, 73, 222))
        buttonYes = Button(label="", style=discord.ButtonStyle.secondary, emoji="✅")
        buttonNo = Button(label="", style=discord.ButtonStyle.secondary, emoji="❌")
        if str(userVote.id) in DataVote:
            em2 = discord.Embed(
                title="RBW Pugs",
                description=f"This user already has an active vote. please do -pugsvote withdraw <user> to remove it.",
                color=discord.Color.from_rgb(255, 255, 255),
            )
            await ctx.reply(embed=em2, ephemeral=True)
            return
        em2 = discord.Embed(
            title="RBW Pugs",
            description=f"Successfully gave {userVote.mention} a vote. ",
            color=discord.Color.from_rgb(255, 255, 255),
        )
        await ctx.reply(embed=em2, ephemeral=True)

        async def buttonYesCallback(di: discord.Interaction):

            with open("Datauser.json", "r") as drr:
                DataUser = json.load(drr)
            if str(di.user.id) in DataUser:
                if str(f"{userVote.id}:1") in DataUser[str(di.user.id)]:
                    DataUser[str(di.user.id)].remove(str(f"{userVote.id}:1"))

                    await di.response.send_message("Your vote has been removed.", ephemeral=True)
                    DataVote[str(userVote.id)] = str(
                        f"{(int(DataVote[str(userVote.id)].split(':')[0]) - 1)}:{':'.join(DataVote[str(userVote.id)].split(':')[1::])}"
                    )
                    print(DataVote[str(userVote.id)])
                else:
                    DataUser[str(di.user.id)].append(str(f"{userVote.id}:1"))
                    await di.response.send_message("You have successfully voted.", ephemeral=True)
                    DataVote[str(userVote.id)] = str(
                        f"{(int(DataVote[str(userVote.id)].split(':')[0]) + 1)}:{':'.join(DataVote[str(userVote.id)].split(':')[1::])}"
                    )
                    print(DataVote[str(userVote.id)])
            else:
                DataUser[str(di.user.id)] = [str(f"{userVote.id}:1")]

                await di.response.send_message("You have successfully voted.", ephemeral=True)
                DataVote[str(userVote.id)] = str(
                    f"{(int(DataVote[str(userVote.id)].split(':')[0]) + 1)}:{':'.join(DataVote[str(userVote.id)].split(':')[1::])}"
                )
            with open("DataUser.json", "w") as tfr:
                json.dump(DataUser, tfr)
            with open("DataVote.json", "w") as wwr:
                json.dump(DataVote, wwr)

        async def buttonNoCallback(di: discord.Interaction):

            with open("Datauser.json", "r") as drr:
                DataUser = json.load(drr)
            if str(di.user.id) in DataUser:
                if str(f"{userVote.id}:0") in DataUser[str(di.user.id)]:
                    DataUser[str(di.user.id)].remove(str(f"{userVote.id}:0"))

                    await di.response.send_message("Your vote has been removed.", ephemeral=True)
                    DataVote[str(userVote.id)] = str(
                        f"{DataVote[str(userVote.id)].split(':')[0]}:{(int(DataVote[str(userVote.id)].split(':')[1]) - 1)}:{':'.join(DataVote[str(userVote.id)].split(':')[2::])}"
                    )
                else:

                    DataUser[str(di.user.id)].append(str(f"{userVote.id}:0"))
                    await di.response.send_message("You have successfully voted.", ephemeral=True)
                    DataVote[str(userVote.id)] = str(
                        f"{DataVote[str(userVote.id)].split(':')[0]}:{(int(DataVote[str(userVote.id)].split(':')[1]) + 1)}:{':'.join(DataVote[str(userVote.id)].split(':')[2::])}"
                    )
            else:
                DataUser[str(di.user.id)] = [str(f"{userVote.id}:0")]

                await di.response.send_message("You have successfully voted.", ephemeral=True)
                DataVote[str(userVote.id)] = str(
                    f"{DataVote[str(userVote.id)].split(':')[0]}:{(int(DataVote[str(userVote.id)].split(':')[1]) + 1)}:{':'.join(DataVote[str(userVote.id)].split(':')[2::])}"
                )
            with open("DataUser.json", "w") as tfr:
                json.dump(DataUser, tfr)
            with open("DataVote.json", "w") as wwr:
                json.dump(DataVote, wwr)

        view = View()
        view.add_item(buttonYes)
        view.add_item(buttonNo)
        buttonYes.callback = buttonYesCallback
        buttonNo.callback = buttonNoCallback
        ddm = await PugsVoteChannel.send(
            embed=EmbedVote, view=view
        )

        DataVote[
            str(userVote.id)
        ] = f"0:0:{datetime.date.today().strftime('%Y:%m:%d')}:{ddm.id}"

        with open("DataVote.json", "w") as wwr:
            json.dump(DataVote, wwr)

    elif query.lower() == "withdraw":
        if str(ctx.message.author.id) in DataVote:
            if ":" in DataVote[str(ctx.message.author.id)]:
                Rrt = DataVote[str(ctx.message.author.id)]
                dateNow = datetime.date.today()
                dateThen = datetime.date(
                    int(Rrt.split(":")[2]),
                    int(Rrt.split(":")[3]),
                    int(Rrt.split(":")[4]),
                )
                dateDelta = (dateNow - dateThen).days  # Credited
                if int(dateDelta) > 7:
                    msga = await pugsvoting.fetch_message(Rrt.split(":")[5])
                    await msga.edit(content=f"{msga.content} **WITHDRAWN**")
                    await msga.clear_reactions()
                    em2 = discord.Embed(
                        title="RBW Pugs",
                        description=f"Your vote has been withdrawn succesfully.",
                        color=discord.Color.from_rgb(255, 255, 255),
                    )
                    await ctx.reply(embed=em2, ephemeral=True)
                    DataVote[str(ctx.message.author.id)] = "0"
                    with open("DataVote.json", "w") as wwr:
                        json.dump(DataVote, wwr)
                else:
                    em2 = discord.Embed(
                        title="RBW Pugs",
                        description=f"You have to wait 7 days since your vote creation date to request another vote.",
                        color=discord.Color.from_rgb(161, 19, 6),
                    )
                    await ctx.reply(embed=em2, ephemeral=True)
            else:
                em2 = discord.Embed(
                    title="RBW Pugs",
                    description=f"You do not have an ongoing vote.",
                    color=discord.Color.from_rgb(255, 255, 255),
                )
                await ctx.reply(embed=em2, ephemeral=True)
        else:
            DataVote[str(ctx.message.author.id)] = "0"
            with open("DataVote.json", "w") as wwr:
                json.dump(DataVote, wwr)

            em2 = discord.Embed(
                title="RBW Pugs",
                description=f"You have been added to the database. Please run the command again.",
                color=discord.Color.from_rgb(255, 255, 255),
            )
            await ctx.reply(embed=em2, ephemeral=True)

    elif query.lower() == "view":
        UserDo = ctx.message.author
        if user is not None:
            if pugsmanager in ctx.message.author.roles:
                UserDo = user
            else:
                em2 = discord.Embed(
                    title="RBW Pugs",
                    description=f"You have to have `PUGS MANAGER` in order to view other people's votes.",
                    color=discord.Color.from_rgb(255, 255, 255),
                )
                await ctx.reply(embed=em2, ephemeral=True)
                return

        if str(UserDo.id) in DataVote:
            if ":" in DataVote[str(UserDo.id)]:
                Rrt = DataVote[str(UserDo.id)]
                YesVote = Rrt.split(":")[0]
                NoVote = Rrt.split(":")[1]
                em2 = discord.Embed(
                    title="RBW Pugs",
                    description=f"Your PUGs vote is:\n> **{YesVote}** ✅ | **{NoVote}** ❌",
                    color=discord.Color.from_rgb(255, 255, 255),
                )
                await ctx.reply(embed=em2, ephemeral=True)
            else:
                em2 = discord.Embed(
                    title="RBW Pugs",
                    description=f"You do not have a PUGs vote.",
                    color=discord.Color.from_rgb(255, 255, 255),
                )
                await ctx.reply(embed=em2, ephemeral=True)
        else:
            DataVote[str(ctx.message.author.id)] = "0"
            with open("DataVote.json", "w") as wwr:
                json.dump(DataVote, wwr)

            em2 = discord.Embed(
                title="RBW Pugs",
                description=f"You have been added to the database. Please run the command again.",
                color=discord.Color.from_rgb(255, 255, 255),
            )
            await ctx.reply(embed=em2, ephemeral=True)


@bot.event
async def on_reaction_add(reaction, user):
    server = bot.get_guild(SERVER_ID)
    PugsVoteChannel = server.get_channel(VOTE_CHANNEL_PUGS)
    if not user.bot:
        with open("DataVote.json", "r") as rt:
            DataVote = json.load(rt)
        if reaction.message.channel.id == PUGS_CONFIRM and reaction.message.author.bot:
            userVote = bot.get_user(int(reaction.message.content))
            print(reaction.message.content)
            if str(userVote.id) in DataVote:
                if (
                        not reaction.message.content == "0"
                        or reaction.message.content == "1"
                ):

                    if reaction.emoji == "✅":
                        em1 = discord.Embed(
                            title=userVote.display_name,
                            description=f"ACCEPTED by {user.display_name}",
                            color=discord.Color.from_rgb(74, 173, 42),
                        )
                        em1.set_author(name="RBW Pugs")
                        await reaction.message.edit(content="1", embed=em1)
                        EmbedVote = discord.Embed(title="RBW PUGs", description=userVote.display_name,
                                                  color=discord.Color.from_rgb(43, 73, 222))
                        buttonYes = Button(label="", style=discord.ButtonStyle.secondary, emoji="✅")
                        buttonNo = Button(label="", style=discord.ButtonStyle.secondary, emoji="❌")

                        async def buttonYesCallback(di: discord.Interaction):

                            with open("Datauser.json", "r") as drr:
                                DataUser = json.load(drr)
                            if str(di.user.id) in DataUser:
                                if str(f"{userVote.id}:1") in DataUser[str(di.user.id)]:
                                    DataUser[str(di.user.id)].remove(str(f"{userVote.id}:1"))

                                    await di.response.send_message("Your vote has been removed.", ephemeral=True)
                                    DataVote[str(userVote.id)] = str(
                                        f"{(int(DataVote[str(userVote.id)].split(':')[0]) - 1)}:{':'.join(DataVote[str(userVote.id)].split(':')[1::])}"
                                    )
                                    print(DataVote[str(userVote.id)])
                                else:
                                    DataUser[str(di.user.id)].append(str(f"{userVote.id}:1"))
                                    await di.response.send_message("You have successfully voted.", ephemeral=True)
                                    DataVote[str(userVote.id)] = str(
                                        f"{(int(DataVote[str(userVote.id)].split(':')[0]) + 1)}:{':'.join(DataVote[str(userVote.id)].split(':')[1::])}"
                                    )
                                    print(DataVote[str(userVote.id)])
                            else:
                                DataUser[str(di.user.id)] = [str(f"{userVote.id}:1")]

                                await di.response.send_message("You have successfully voted.", ephemeral=True)
                                DataVote[str(userVote.id)] = str(
                                    f"{(int(DataVote[str(userVote.id)].split(':')[0]) + 1)}:{':'.join(DataVote[str(userVote.id)].split(':')[1::])}"
                                )
                            with open("DataUser.json", "w") as tfr:
                                json.dump(DataUser, tfr)
                            with open("DataVote.json", "w") as wwr:
                                json.dump(DataVote, wwr)

                        async def buttonNoCallback(di: discord.Interaction):

                            with open("Datauser.json", "r") as drr:
                                DataUser = json.load(drr)
                            if str(di.user.id) in DataUser:
                                if str(f"{userVote.id}:0") in DataUser[str(di.user.id)]:
                                    DataUser[str(di.user.id)].remove(str(f"{userVote.id}:0"))

                                    await di.response.send_message("Your vote has been removed.", ephemeral=True)
                                    DataVote[str(userVote.id)] = str(
                                        f"{DataVote[str(userVote.id)].split(':')[0]}:{(int(DataVote[str(userVote.id)].split(':')[1]) - 1)}:{':'.join(DataVote[str(userVote.id)].split(':')[2::])}"
                                    )
                                else:

                                    DataUser[str(di.user.id)].append(str(f"{userVote.id}:0"))
                                    await di.response.send_message("You have successfully voted.", ephemeral=True)
                                    DataVote[str(userVote.id)] = str(
                                        f"{DataVote[str(userVote.id)].split(':')[0]}:{(int(DataVote[str(userVote.id)].split(':')[1]) + 1)}:{':'.join(DataVote[str(userVote.id)].split(':')[2::])}"
                                    )
                            else:
                                DataUser[str(di.user.id)] = [str(f"{userVote.id}:0")]

                                await di.response.send_message("You have successfully voted.", ephemeral=True)
                                DataVote[str(userVote.id)] = str(
                                    f"{DataVote[str(userVote.id)].split(':')[0]}:{(int(DataVote[str(userVote.id)].split(':')[1]) + 1)}:{':'.join(DataVote[str(userVote.id)].split(':')[2::])}"
                                )
                            with open("DataUser.json", "w") as tfr:
                                json.dump(DataUser, tfr)
                            with open("DataVote.json", "w") as wwr:
                                json.dump(DataVote, wwr)

                        view = View()
                        view.add_item(buttonYes)
                        view.add_item(buttonNo)
                        buttonYes.callback = buttonYesCallback
                        buttonNo.callback = buttonNoCallback
                        ddm = await PugsVoteChannel.send(
                            embed=EmbedVote, view=view
                        )

                        DataVote[
                            str(userVote.id)
                        ] = f"0:0:{datetime.date.today().strftime('%Y:%m:%d')}:{ddm.id}"
                    elif reaction.emoji == "❌":

                        em1 = discord.Embed(
                            title=userVote.display_name,
                            description=f"DENIED by {user.display_name}",
                            color=discord.Color.from_rgb(117, 8, 8),
                        )
                        em1.set_author(name="RBW Pugs")
                        await reaction.message.edit(content="0", embed=em1)
                        DataVote[str(userVote.id)] = "0"

                    with open("DataVote.json", "w") as wwr:
                        json.dump(DataVote, wwr)
                    await reaction.message.clear_reactions()
        if (
                reaction.message.channel.id == CONFIRM_STRIKE_CHANNEL
                and reaction.message.author.bot
        ):
            if reaction.emoji == "✅":
                await reaction.message.reply(embed=discord.Embed(description=f"{user.mention} has accepted this request! Please give out a punishment using:\n\n`=strike {reaction.message.content.split(':')[1]}`",
                                                                 color=0x4b61df
                                                                 ))
                await reaction.message.edit(embed=discord.Embed(description=f"**Report Details**\n\n Accepted by {user.mention}",
                                                                color=discord.Color.from_rgb(0, 234, 20)))
                await reaction.message.clear_reactions()

            elif reaction.emoji == "❌":
                await reaction.message.reply(
                    embed=discord.Embed(description=f"{user.mention} has denied this request!",
                                        color=0x4b61df))
                await reaction.message.edit(
                    embed=discord.Embed(description=f"**Report Details**\n\n Denied by {user.mention}",
                                        color=discord.Color.from_rgb(234, 0, 20)))
                await reaction.message.clear_reactions()


@bot.command(
    name="pugstourney",
    description="Pugs tournament",
    aliases=["tourney", "tournament"]
)
@commands.has_role(PUGS_MANAGER_ROLE)
async def pugstourney(ctx, setting: str, id=None, memberSet: str = None):
    with open("DataTourney.json", "r") as jh:
        DataTourney = json.load(jh)
    if setting.lower() == "create":
        while True:

            NumberTourneyId = random.randint(1000, 100000)
            if not str(NumberTourneyId) in DataTourney:
                break
        DataTourney[str(NumberTourneyId)] = {"host": str(ctx.message.author.id), "status": "-1", "members": [],
                                             "winners": []}
        em2 = discord.Embed(
            title="RBW Tournaments",
            description=f"You have successfully created a PUGs tournament.\n**Tournament ID: {NumberTourneyId}**\nPlease do .pugstourney view <id> to view your tournament,\nPlease do .pugstourney winner <winners seperated in commans(,)> to set the winners for the tournament,\nPlease do .pugstourney delete <id> to delete the tournament,\nPlease do .pugstourney status <-1(pending, just created) - 0(Currently in play) - 1(Finished)> to set the status of the tournament,\n Please do .pugstourney members <Players seperated by ' '(space) and teams seperated by a new line> to set the members of the tournament.",
            color=discord.Color.from_rgb(255, 255, 255),
        )
        await ctx.reply(embed=em2, ephemeral=True)
    elif setting.lower() == "delete":
        if id is not None and id in DataTourney:

            DataTourney.pop(str(id))
            em2 = discord.Embed(
                title="RBW Tournaments",
                description=f"Successfully deleted Tournament #{id}",
                color=discord.Color.from_rgb(255, 255, 255),
            )
            await ctx.reply(embed=em2, ephemeral=True)
        else:
            em2 = discord.Embed(
                title="RBW Tournaments",
                description=f"Tournament does not exist.",
                color=discord.Color.from_rgb(255, 255, 255),
            )
            await ctx.reply(embed=em2, ephemeral=True)
    elif setting.lower() == "list":
        Tourneyslist = []
        for v in DataTourney:
            Tourneyslist.append(f" [{v}:<@{DataTourney[v]['host']}>] ")
        em2 = discord.Embed(
            title="RBW Tournaments",
            description=f"List of tournaments (id:host):\n\n{'  '.join(Tourneyslist)}",
            color=discord.Color.from_rgb(255, 255, 255),
        )
        await ctx.reply(embed=em2, ephemeral=True)
    elif setting.lower() == "view":
        print(id)
        if id is not None and str(id) in DataTourney:
            em2 = discord.Embed(
                title="RBW Tournaments",
                description=f"Tournament #{id}\n> **Host**: <@{DataTourney[id]['host']}>\n> **Status**: {DataTourney[id]['status']}\n> **Members**: {' '.join(DataTourney[id]['members'])}\n> **Winners**: {' '.join(DataTourney[id]['winners'])}",
                color=discord.Color.from_rgb(255, 255, 255),
            )
            await ctx.reply(embed=em2, ephemeral=True)

        elif '<@' in id:
            id = id.strip('<@>')
            WonTourneys = []
            for vs in DataTourney:
                if id in DataTourney[vs]['winners']:
                    WonTourneys.append(vs)
            em2 = discord.Embed(
                title="RBW Tournaments",
                description=f"User's won tournaments: ({len(WonTourneys)})\n{' -- '.join(WonTourneys)}",
                color=discord.Color.from_rgb(255, 255, 255),
            )
            await ctx.reply(embed=em2, ephemeral=True)
        else:
            em2 = discord.Embed(
                title="RBW Tournaments",
                description=f"Tournament does not exist.",
                color=discord.Color.from_rgb(255, 255, 255),
            )
            await ctx.reply(embed=em2, ephemeral=True)
    elif setting.lower() == "winner":
        if id is not None and id in DataTourney:
            if memberSet is not None and ',' in memberSet:

                winnerSets = memberSet.split(",")
                DataTourney[id]['winners'] = winnerSets
                em2 = discord.Embed(
                    title="RBW Tournaments",
                    description=f"Successfully set winners.",
                    color=discord.Color.from_rgb(255, 255, 255),
                )
                await ctx.reply(embed=em2, ephemeral=True)
            else:
                em2 = discord.Embed(
                    title="RBW Tournaments",
                    description=f"Error while seperating members: Please include a users arguement with Commas (,) seperating each user id.",
                    color=discord.Color.from_rgb(255, 255, 255),
                )
                await ctx.reply(embed=em2, ephemeral=True)
        else:
            em2 = discord.Embed(
                title="RBW Tournaments",
                description=f"Tournament does not exist.",
                color=discord.Color.from_rgb(255, 255, 255),
            )
            await ctx.reply(embed=em2, ephemeral=True)
    elif setting.lower() == "members":
        if id is not None and id in DataTourney:
            if memberSet is not None and ' ' in memberSet:
                if '\n' in memberSet:
                    memberSet = ' '.join(memberSet.split('\n'))
                memberSets = memberSet.split(" ")

                DataTourney[id]['members'] = memberSets
                em2 = discord.Embed(
                    title="RBW Tournaments",
                    description=f"Successfully set members.",
                    color=discord.Color.from_rgb(255, 255, 255),
                )
                await ctx.reply(embed=em2, ephemeral=True)
            else:
                em2 = discord.Embed(
                    title="RBW Tournaments",
                    description=f"Error while seperating members: Please include a users arguement with Spaces ( ) seperating each username.",
                    color=discord.Color.from_rgb(255, 255, 255),
                )
                await ctx.reply(embed=em2, ephemeral=True)
        else:
            em2 = discord.Embed(
                title="RBW Tournaments",
                description=f"Tournament does not exist.",
                color=discord.Color.from_rgb(255, 255, 255),
            )
            await ctx.reply(embed=em2, ephemeral=True)
    elif setting.lower() == "status":
        if id is not None and id in DataTourney:
            if memberSet is not None:
                if memberSet == "-1" or memberSet == "0" or memberSet == "1":
                    DataTourney[id]["status"] = memberSet
                    em2 = discord.Embed(
                        title="RBW Tournaments",
                        description=f"Set Status {memberSet} for Tournament #{id}.",
                        color=discord.Color.from_rgb(255, 255, 255),
                    )
                    await ctx.reply(embed=em2, ephemeral=True)
                else:
                    em2 = discord.Embed(
                        title="RBW Tournaments",
                        description=f"Accepted Status Arguements: -1(Pending), 0(Ongoing), 1(Finished)",
                        color=discord.Color.from_rgb(255, 255, 255),
                    )
                    await ctx.reply(embed=em2, ephemeral=True)
            else:
                em2 = discord.Embed(
                    title="RBW Tournaments",
                    description=f"Please Provide a status.",
                    color=discord.Color.from_rgb(255, 255, 255),
                )
                await ctx.reply(embed=em2, ephemeral=True)
        else:
            em2 = discord.Embed(
                title="RBW Tournaments",
                description=f"Tournament does not exist.",
                color=discord.Color.from_rgb(255, 255, 255),
            )
            await ctx.reply(embed=em2, ephemeral=True)
    else:
        em2 = discord.Embed(
            title="RBW Tournaments",
            description=f"Unrecognized Arguement! Accepted arguements: .pugstourney <view/create/delete/status/members/winner>",
            color=discord.Color.from_rgb(255, 255, 255),
        )
        await ctx.reply(embed=em2, ephemeral=True)
    with open("DataTourney.json", "w") as hjgh:
        json.dump(DataTourney, hjgh)


@bot.command(
    name="strikerequest",
    description="Create a strike request",
    aliases=["sr", "srequest"],
)
async def strikerequest(ctx, user: discord.Member, proof, reason=None):
    server = bot.get_guild(SERVER_ID)
    StrikeConfirm = server.get_channel(CONFIRM_STRIKE_CHANNEL)
    if "https://" in proof:
        if reason is not None:
            em2 = discord.Embed(
                description=f"Thank you for your report! Our team will look into it, and if necessary, we will apply a punishment.",
                color=0x4b61df,
            )
            await ctx.reply(embed=em2, ephemeral=True)
            em3 = discord.Embed(
                description=f"Report Details\n\n **Request**: {ctx.message.author.mention}\n **Target**: {user.mention}\n **Reason**: {reason}\n **Proof**: {proof}",
                color=0x4b61df,
            )
            msgj = await StrikeConfirm.send(
                content=f"{ctx.message.author.id}:{user.id}", embed=em3
            )
            await msgj.add_reaction("✅")
            await msgj.add_reaction("❌")

        else:
            em2 = discord.Embed(
                description=f"Please include a reason.",
                color=0x4b61df,
            )
            await ctx.reply(embed=em2, ephemeral=True)
    else:
        if reason is None:
            if ctx.message.attachments:
                em2 = discord.Embed(
                    description=f"Thank you for your report! Our team will look into it, and if necessary, we will apply a punishment.",
                    color=0x4b61df,
                )
                await ctx.reply(embed=em2, ephemeral=True)
                em3 = discord.Embed(
                    description=f"**REPORT DETAILS**\n\n **Request**: {ctx.message.author.mention}\n **Target**: {user.mention}\n **Reason**: {proof}\n **Proof**:",
                    color=0x4b61df,
                )
                em3.set_image(url=ctx.message.attachments[0].url)
                msgj = await StrikeConfirm.send(
                    content=f"{ctx.message.author.id}:{user.id}", embed=em3
                )
                await msgj.add_reaction("✅")
                await msgj.add_reaction("❌")
            else:
                em2 = discord.Embed(
                    description=f"Please attach proof.",
                    color=0x4b61df,
                )
                await ctx.reply(embed=em2, ephemeral=True)
        else:
            em2 = discord.Embed(
                description=f"Please include a valid url.",
                color=0x4b61df,
            )
            await ctx.reply(embed=em2, ephemeral=True)

asyncio.run(bot.load_extension('cogs.tourney'))
bot.prefix = '-'
with open('.key', 'r') as key:
    bot.run(key.read())
