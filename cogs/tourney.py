import json
import io
import traceback

import discord
from discord.ext import commands

from api import API, APIError
from .render import leaderboard

constants = None
with open("tourney.constants.json", "r", encoding="utf-8") as rt:
    rt.seek(0)
    constants = json.load(rt)

teams_file = 'data/teams.json'
players_file = 'data/players.json'
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
        self.teams = json.load(open(teams_file, 'r'))
        self.players = json.load(open(players_file, 'r'))

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

        description = """**Team Commands** - Mange your team
`-create [team name]` Create a new team. You will be the team leader.
`-invite [player]` Invite a player to your team.
`-accept [team name]` Accept an invite to a team.
`-reject [team name]` Reject an invite to a team.
`-uninvite [team name]` Sike! I don't want you on my team.
`-leave` Leave your current team D:
`-disband [team name]` Fed up with your team losing? Use this one!
"""

        if isManager:
            description += """\n\n**Manager Commands** - You're managing the tournament, lucky you.
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
    async def disband(self, ctx, *args):

        team_name = " ".join(args)

        if team_name == "":
            return await self.reply_generic(ctx, f'To confirm, state the name of your team by running `{self.bot.prefix}disband <team_name>`')

        await self.api.disbandTeam(team_name, ctx.author.id)

        return await self.reply_generic(ctx, f'You have successfully disbanded `{team_name}`.')

    @commands.command(name = 'kick', aliases = ['remove'], usage = 'kick <DiscordID>')
    @commands.cooldown(rate = 3, per = 3)
    async def kick(self, ctx, player: discord.User):

        await self.api.kickMember(player.id, ctx.author.id)

        return await self.reply_generic(ctx, f'<@{player.id}> has been kicked.')

    @commands.command(name = 'info', aliases = ['i'])
    async def info(self, ctx, player: discord.User):

        team = await self.api.getUserTeam(player.id)

        return await self.get_team_info(ctx, team)

    @commands.command(name = 'team')
    async def team(self, ctx, *args):

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

        ignoreLocked = ignore == "bypass"

        if not isLocked and not ignoreLocked:
            return await self.reply_error(ctx, "Scoring has not yet completed for this bracket.")

        scores = await self.api.getBracketScores(bracket)

        img = await leaderboard(ctx, scores)
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
    

    async def announce(self, ctx, message):
        channel = discord.utils.get(ctx.guild.channels, id=announce_channel)
        return await channel.send(message)

    async def reply_generic(self, ctx, message):
        return await ctx.message.reply(embed=self.get_embed(message), mention_author=False)

    async def reply_error(self, ctx, message):
        return await ctx.message.reply(embed=discord.Embed(
            description = message,
            color = 0xff0000,
        ).set_footer(text = "BedWars Championship's Tourney"), mention_author=False)

    def get_embed(self, description):
        return discord.Embed(
            description = description,
            color = 0x4b61df,
        ).set_footer(text = "BedWars Championship's Tourney")

    @commands.command(name = 'help2')
    async def help(self, ctx):
        await ctx.send("Choose an option:", view=SelectView())

class Select(discord.ui.Select):
    def __init__(self):
        options = [
        discord.SelectOption(label="General", description="Showcases General Commands"),
        discord.SelectOption(label="Management", description="Showcases Management's Commands.")
    ]
        super().__init__(placeholder="Select an option", max_values=1, min_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):

        if self.values[0] == "General":
            embed1 = discord.Embed(
                title = "**General**",
                description = f"**Create ** your Team using `-create` *<TeamName>. Alias: create.*\n**Disband** your Team using `-disband` *<TeamName>. Alias: abandon.*\n\n**Invite** a Player using `-invite` *<DiscordTAG/ID>. Alias: add.*\n**Uninvite** a Player using `-uninvite` *<DiscordTAG/ID>.*\n\n**Accept** a Team Invitation using `-accept` *<TeamName>. Alias: join.*\n**Reject** a Team Invitation using `-reject` *<TeamName>.*\n**Leave** a Team using `-leave` *<TeamName>.*\n\nGet **Info** on a Player using `-info` *<DiscordTAG/ID>. Alias: i.*",
                color = 0x4b61df
            )
            await interaction.response.send_message(embed=embed1, ephemeral=True)

        if interaction.guild and any(role.id == manager_role for role in interaction.user.roles):

            if self.values[0] == "Management":
                embed2 = discord.Embed(
                    title = "**Management**",
                    description = "**Kick a Team** from Sign Ups using `-kickteam` *<TeamName>.*\n\nSet a **Maximum Amount of Players** per Team using `-setmaxplayers` <Number>.*\n\nSet a **Maximum Amount of Teams** using `-setmaxteams` *<Number>.*\n\n**Clear Games** using `-cleargames` *<>.*",
                    color = 0x4b61df
                )
                await interaction.response.send_message(embed=embed2, ephemeral=True)
            else:
                await interaction.response.send_message(content="Access denied.", ephemeral=True)

class SelectView(discord.ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)
        self.add_item(Select())

async def setup(bot):
    await bot.add_cog(Tourney(bot))
