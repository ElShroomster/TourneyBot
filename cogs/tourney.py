import asyncio
import json
import io
import traceback
from typing import Optional

import discord
from discord.ext import commands

from api import API, APIError
from .render import leaderboard

constants = None
with open("tourney.constants.json", "r", encoding="utf-8") as rt:
    rt.seek(0)
    constants = json.load(rt)


max_teams_default = 64
max_players_default = 2
max_name_len = 32

allowed_channels = constants["ALLOWED_CHANNELS"]
announce_channel = constants["ANNOUNCEMENTS_CHANNEL"]
manager_role = constants["MANAGER_ROLE"]
bwcs_role = constants["TOURNEY_ROLE"]

valid_tags = ["QUAL1", "QUAL2", "QUAL3", "QUAL4", "QUAL5", "QUAL6", "QUAL7", "QUAL8"]

class Tourney(commands.Cog):
    def __init__(self, bot):

        self.api: API = bot.api
        self.bot = bot
        self.max_name_len = max_name_len

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        
        if isinstance(error, commands.CommandNotFound):
            return
        
        e = error.original if hasattr(error, "original") else error
        
        # Catch API request failures
        if isinstance(e, APIError):
            return await self.reply_error(ctx, e) 
        
        print(''.join(traceback.TracebackException.from_exception(e).format()))
        
        return await self.reply_error(ctx, f'Error:\n{error}') 
    
    @commands.command(name = 'help')
    async def help_basic(self, ctx):

        isManager = discord.utils.get(ctx.guild.roles, id=manager_role) in ctx.author.roles

        description = """**Team Commands** - Manage your team
`-invite [@user]` - Invites a player to join your team
`-uninvite [@user]` - Cancel your invite to a player (lol)
`-accept [team name]` - Accepts an invitation to join a team
`-reject [team name]` - Rejects an invitation to join a team
`-leave [team name]` - Leaves your current team
`-kick [@user]` - Kicks a player from your team
`-disband [team name]` - Disbands team
`-info/-i [team/@user]` - Get info on a team/player's team
`-lb/-standings [bracket]` - Shows a leaderboard for the current standings in a bracket
`-team [team name]` - Variation of -i, check the info of a team
`-thanks` - Thanks the developers & designers for their hard work ❤
"""

        if isManager:
            description += """\n\n**Manager Commands** - You're managing the tournament, lucky you.
`-api` - Check if the API is online
`-forcedisband [team name]` - Forcefully disbands & DQs a team
`-lock? [bracket]` - Checks the lock status of the bracket
`-lock [bracket]` - Prevents any further modification to bracket scores, allows lb to be displayed
`-unlock [bracket]` - Allows further modification to bracket scores, prevents lb from being displayed
`-lb/-standings [bracket] bypass` - Forcefully shows a leaderboard for the current standings in a bracket regardless of lock status
`-score? [bracket] [team name]` - Checks the score acquired by a team in chosen bracket
`-score [bracket] [team name] [final|bed|pos|time OR f|b|p|t] [quantity]` - Simply input the finals, beds, position or time. The value for time you provide should be in minutes.
`-config` - Check the current config settings
`-config players [number]` - Sets maximum amt of players per team
`-config teams [number]` - Sets maximum amt of teams in tourney
"""

        embed = discord.Embed(
            title= "Help Menu",
            description = description,
            color = 0x4b61df,
        ).set_footer(text = "BedWars Championship's Tourney")

        await ctx.message.reply(embed=embed, mention_author=False)
    
    @commands.command(name = 'api')
    async def check_api(self, ctx):
        
        isOnline = await self.api.getStatus()

        await self.reply_generic(ctx, 'Online!' if isOnline else 'API Down D:')

    @commands.command(name = 'create')
    @commands.cooldown(rate = 1, per = 3)
    async def register(self, ctx, *args):
        if len(args) == 0:
            return await self.reply_error(ctx, 'You must state a team name.')

        team_name = " ".join(args)
        if len(team_name) > self.max_name_len:
            return await self.reply_error(ctx, 'Your team name is too long, the max length is {self.max_name_len} characters.')

        await self.api.createTeam(team_name, ctx.author.id)

        await ctx.author.add_roles(discord.utils.get(ctx.guild.roles, id = bwcs_role))
        return await self.reply_generic(ctx, f'Team `{team_name}` has been created. Use: `{self.bot.prefix}invite <user>` to invite a friend.')

    @commands.command(name = 'invite', aliases = ['add'], usage = 'invite <DiscordID>')
    @commands.cooldown(rate = 3, per = 3)
    async def invite(self, ctx, player: discord.User):

        team = await self.api.getUserTeam(ctx.author.id)

        await self.api.inviteToTeam(player.id, ctx.author.id)

        return await self.reply_generic(ctx, f'<@{player.id}> has been invited to `{team["name"]}`\n'f'To accept this invite, they must run `{self.bot.prefix}accept {team["name"]}`')

    @commands.command(name = 'accept', aliases = ['join'])
    @commands.cooldown(rate = 3, per = 3)
    async def accept(self, ctx, *args):

        team_name = " ".join(args)
        
        await self.api.acceptInvite(team_name, ctx.author.id)
        members = await self.api.getTeamMembers(team_name)

        print(members)

        await self.announce(ctx, f"`{team_name}` has entered the tournament.\nMembers: ...")
        await ctx.author.add_roles(discord.utils.get(ctx.guild.roles, id=bwcs_role))
        return await self.reply_generic(ctx, f'You have successfully joined `{team_name}`')
    
    @commands.command(name = 'uninvite')
    async def uninvite(self, ctx, player: discord.User):
        
        await self.api.withdrawInvite(player.id, ctx.author.id)

        return await self.reply_generic(ctx, f'<@{player.id}> has been uninvited')
    
    @commands.command(name = 'reject')
    async def reject(self, ctx, *args):
        team_name = " ".join(args)

        await self.api.rejectInvite(team_name, ctx.author.id)

        return await self.reply_generic(ctx, f'You have rejected `{team_name}`.')

    @commands.command(name = 'leave', usage = 'leave <team_name>')
    @commands.cooldown(rate = 3, per = 3)
    async def leave(self, ctx):
        team = await self.api.getUserTeam(ctx.author.id)
        team_name = team["name"]

        await self.api.leaveTeam(team_name, ctx.author.id)

        return await self.reply_generic(ctx, f'You have successfully left `{team_name}`')

    @commands.command(name = 'disband', aliases = ['abandon'], usage = 'disband <team_name>')
    async def disband(self, ctx):
        await ctx.send("https://www.youtube.com/watch?v=H5d42w4ZcY4", view=ConfirmDisbandView(self.bot, self.api, ctx))


    @commands.command(name = 'kick', aliases = ['remove'], usage = 'kick <DiscordID>')
    @commands.cooldown(rate = 3, per = 3)
    async def kick(self, ctx, player: discord.User):

        await self.api.kickMember(player.id, ctx.author.id)

        return await self.reply_generic(ctx, f'<@{player.id}> has been kicked.')

    @commands.command(name = 'info', aliases = ['i'])
    async def info(self, ctx, player: discord.User):

        team = await self.api.getUserTeam(player.id)

        return await self.get_team_info(ctx, team)

    @commands.command(name = 'teams')
    async def team(self, ctx):

        teams = await self.api.getTeams()
        msg = ""

        for i,team in enumerate(teams):
            msg += str(i) + ": " + team["name"] + "\n"

        return await self.reply_generic(ctx, msg)

    @commands.command(name = 'team')
    async def teams(self, ctx, *args):

        team_name = " ".join(args)

        team = await self.api.getTeam(team_name)

        return await self.get_team_info(ctx, team)

    async def get_team_info(self, ctx, team):
        members = await self.api.getTeamMembers(team["name"])
        invites = await self.api.getTeamPending(team["name"])

        member_strings = []
        for member in members:
            
            uid = member["userId"]

            user = await ctx.guild.fetch_member(int(uid))

            if uid == team["leader"]:
                member_strings.append(f':crown: {user}')
            else:
                member_strings.append(f'{user}')

        
        invite_strings = []
        for invite in invites:
            
            uid = invite["userId"]

            user = await ctx.guild.fetch_member(int(uid))

            invite_strings.append(f'{user}')
                
        string = ''
        string += f'**Team Name**: `{team["name"]}`\n'
        string += f'**Members**: {",".join(member_strings)}\n'

        if len(invite_strings) == 0:
            string += f'**Pending**: None'
        else:
            string += f'**Pending**: {",".join(invite_strings)}\n'

        embed = discord.Embed(
            title = "Team Information",
            description = string,
            color = 0x4b61df,
        ).set_footer(text = "BedWars Championship's Tourney")

        return await ctx.message.reply(embed=embed, mention_author=False)

    @commands.command(name = 'standings', aliases = ['lb'])
    async def standings(self, ctx, bracket, ignore=""):

        status = await self.api.getBracketStatus(bracket)
        isLocked = status["isLocked"]

        isManager = discord.utils.get(ctx.guild.roles, id=manager_role) in ctx.author.roles
        ignoreLocked = ignore == "bypass" and isManager

        if not isLocked and not ignoreLocked:
            return await self.reply_error(ctx, "Scoring has not yet completed for this bracket.")

        scores = await self.api.getBracketScores(bracket)

        img = await leaderboard(ctx, scores, bracket)
        image_file = discord.File(io.BytesIO(img),filename=f"lb.png")
        
        if not isLocked:
            await ctx.send(embed=discord.Embed(
                description = "**WARNING**\nScoring is not yet complete, this leadboard may not be accurate.",
                color = 0xff0000,
            ), file=image_file)
        else:
            await ctx.send(file=image_file)

    @commands.group(invoke_without_command=True, name="config")
    async def config(self, ctx):

        players = await self.api.getConfig("max_players")
        teams = await self.api.getConfig("max_teams")
        
        await self.reply_generic(ctx, f'`max_players={players["value"]}`\n`max_teams={teams["value"]}`')

    @config.command(name = 'players')
    async def config_max_players(self, ctx, max_players=None):

        if max_players is None:
            max = await self.api.getConfig("max_players")

            return await self.reply_generic(ctx, f'Max players set to {max["value"]}.')
        
        if not discord.utils.get(ctx.guild.roles, id=manager_role) in ctx.author.roles:
            return await self.reply_error(ctx, f'You are not a manager. Only managers can set max players.')
        
        await self.api.setConfig("max_players", int(max_players))

        return await self.reply_generic(ctx, f'Max players set to {max_players}.')
    
    @config.command(name = 'teams')
    async def config_max_teams(self, ctx, max_players=None):

        if max_players is None:
            max = await self.api.getConfig("max_teams")

            return await self.reply_generic(ctx, f'Max teams set to {max["value"]}.')
        
        if not discord.utils.get(ctx.guild.roles, id=manager_role) in ctx.author.roles:
            return await self.reply_error(ctx, f'You are not a manager. Only managers can set max players.')
        
        await self.api.setConfig("max_teams", int(max_players))

        return await self.reply_generic(ctx, f'Max teams set to {max_players}.')


    @commands.command(name = 'forcedisband')
    async def kick_team(self, ctx, *args):

        if not discord.utils.get(ctx.guild.roles, id=manager_role) in ctx.author.roles:
            return await self.reply_error(ctx, f'You are not a manager. Only managers can kick teams.')

        team_name = " ".join(args)

        if team_name == "":
            return await self.reply_error(f'Please enter the team name: `{self.bot.prefix}forcedisband <team_name>`')

        await self.api.forceDisband(team_name, ctx.author.id)

        await self.announce(ctx, f"`{team_name}` has been removed from the tourney by <@{ctx.author.id}>")

        return await self.reply_generic(ctx, f'Successfully removed team `{team_name}`')

    @commands.command(name = 'score')
    async def add_points(self, ctx, bracket, team, category, quantity=None):

        if not discord.utils.get(ctx.guild.roles, id=manager_role) in ctx.author.roles:
            return await self.reply_error(ctx, f'Permission denied.')
        
        bracket = bracket.lower()

        brackets = ["qual1", "qual2", "qual3", "qual4", "qual5", "qual6", "qual7", "qual8", "semi1", "semi2", "semi3", "semi4", "finals"]

        cat_maps = {
            "b": "bed",
            "f": "final",
            "p": "pos",
            "t": "time"
        }

        cat_fn_map = {
            "bed": self.api.scoreBeds,
            "final": self.api.scoreFinals,
            "pos": self.api.scorePos,
            "time": self.api.scoreTime,
        }

        if bracket not in brackets:
            return await self.reply_error(ctx, f'Bracket not found in {",".join(brackets)}')
        
        if category in cat_maps:
            category = cat_maps[category]
        
        if category not in cat_fn_map:
            return await self.reply_error(ctx, f'Category not found in {",".join(cat_fn_map.keys())}')
        
        notes = []

        if quantity is None:
            notes.append(f'Assumed value of 1 for {category}')
            quantity = 1
        
        fn = cat_fn_map[category]

        res = await fn(team, bracket, quantity)

        return await self.send_score(ctx, res)

    @commands.command(name='score?')
    async def check_points(self, ctx, bracket, team):
        res = await self.api.checkScore(team, bracket)

        await self.send_score(ctx, res)

    @commands.command(name='lock')
    async def lock(self, ctx, bracket):
        
        if not discord.utils.get(ctx.guild.roles, id=manager_role) in ctx.author.roles:
            return await self.reply_error(ctx, f'Permission denied.')
        
        await self.api.changeBracketLock(bracket, True)

        await self.reply_generic(ctx, f'Bracket `{bracket}` has been locked.')

    @commands.command(name='unlock')
    async def unlock(self, ctx, bracket):
        
        if not discord.utils.get(ctx.guild.roles, id=manager_role) in ctx.author.roles:
            return await self.reply_error(ctx, f'Permission denied.')
        
        await self.api.changeBracketLock(bracket, False)

        await self.reply_error(ctx, f'**WARNING**\n\nBracket `{bracket}` has been unlocked.\n\nScores could be modifed.')

    @commands.command(name='lock?')
    async def check_lock(self, ctx, bracket):
        
        if not discord.utils.get(ctx.guild.roles, id=manager_role) in ctx.author.roles:
            return await self.reply_error(ctx, f'Permission denied.')
        
        status = await self.api.getBracketStatus(bracket)
        isLocked = status["isLocked"]

        await self.reply_generic(ctx, f'Bracket {"is locked." if isLocked else "is unlocked."}')


    async def send_score(self, ctx, score):
        pos = score["position"]
        sur = score["survival"]
        fin = score["finals"]
        bed = score["bedBreaks"]

        x = {
            "Bracket": score["stage"],
            "Team ID": score["teamId"],
            "Position": f'{pos} points',
            "Time Survived": f'{sur} points',
            "Total Finals": f'{fin} points',
            "Total Beds": f'{bed} points',
            "Total Points": sum([pos, sur, fin, bed])
        }

        return await self.reply_generic(ctx, "\n".join([f'**{k}**: {v}' for k,v in x.items()]))
    
    @commands.command(name = 'thanks', aliases=["ty"])
    async def ty(self, ctx):
        await ctx.send("You are so welcome.", view=Credits(self.bot))

    @commands.command(name = 'sync')
    async def sync(self, ctx: commands.Context):

        attach = ctx.message.attachments

        if not discord.utils.get(ctx.guild.roles, id=manager_role) in ctx.author.roles:
            return await self.reply_error(ctx, f'Permission denied.')

        if len(attach) != 1:
            return await self.reply_error(ctx, "Please attach the teams.json file to import.")
        
        a = attach[0]

        if not a.filename.endswith(".json"):
            return await self.reply_error(ctx, f'Must be a `.json` file.')
        
        data = json.loads(await a.read())

        return await ctx.send("", view=ConfirmSync(ctx, self.api, data))


    async def announce(self, ctx, message):
        channel = discord.utils.get(ctx.guild.channels, id=announce_channel)
        return await channel.send(message)

    async def reply_generic(self, ctx, message):
        return await ctx.message.reply(embed=self.get_embed(message), mention_author=False)
    
    def get_embed(self, description):
        return discord.Embed(
            description = description,
            color = 0x4b61df,
        ).set_footer(text = "BedWars Championship's Tourney")

    async def reply_error(self, ctx, message):
        return await ctx.message.reply(embed=discord.Embed(
            description = message,
            color = 0xff0000,
        ).set_footer(text = "BedWars Championship's Tourney"), mention_author=False)

class ConfirmSync(discord.ui.View):

    def __init__(self, ctx: commands.Context, api: API, teams):
        self.ctx = ctx
        self.api = api
        self.teams = teams
        super().__init__(timeout=60)

    @discord.ui.button(label="I confirm that I want to sync this file.", style=discord.ButtonStyle.danger) 
    async def button_callback(self, interaction: discord.Interaction, button):

        if self.ctx.author.id != interaction.user.id:
            return

        await interaction.response.send_message(f'Sync in progress...') 

        size = len(self.teams)

        for i, t in enumerate(self.teams):
            await self.api.createTeam(t["name"], t["leader"])

            for m in t["members"]:
                await self.api.inviteToTeam(m, t["leader"])
                await self.api.acceptInvite(t["name"], m)

            if i % 10 == 0:
                await self.ctx.channel.send(f'{i + 1}/{size} ({t["name"]})')

        await self.ctx.channel.send(f'Sync completed. All teams updated.')
            


class ConfirmDisbandView(discord.ui.View):

    def __init__(self, bot: commands.Bot, api: API, ctx):
        self.bot = bot
        self.api = api
        self.ctx = ctx
        super().__init__(timeout=60)

    @discord.ui.button(label="I understand that my actions have consequences.", style=discord.ButtonStyle.danger) 
    async def button_callback(self, interaction: discord.Interaction, button):

        if self.ctx.author.id != interaction.user.id:
            return
       
        team = await self.api.getUserTeam(interaction.user.id)

        team_name = team["name"]

        await self.api.disbandTeam(team_name, self.ctx.author.id)

        await interaction.response.send_message(f'Say goodbye to team {team_name}') 

        channel = discord.utils.get(self.ctx.guild.channels, id=announce_channel)
        return await channel.send(f"Team `{team_name}` has been disbanded")


class Credits(discord.ui.View):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__(timeout=60)

    @discord.ui.button(label="Credits", style=discord.ButtonStyle.primary, emoji='❤') 
    async def button_callback(self, interaction: discord.Interaction, button):

        user1 = await self.bot.fetch_user(722011064467849218)
        user2 = await self.bot.fetch_user(1100176389476450374)

        dm1 = await self.bot.create_dm(user1)
        dm2 = await self.bot.create_dm(user2)

        message = f'Thanks. From {interaction.user.global_name} {interaction.user.mention}'

        await interaction.response.send_message("Made by moonib, ohb00 & theo <3.", ephemeral=True) 
        await dm1.send(message)
        await dm2.send(message)



async def setup(bot):
    await bot.add_cog(Tourney(bot))
