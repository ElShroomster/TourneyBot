from discord.ext import commands
import discord
import json

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
manager_roles = constants["MANAGER_ROLES"]
admin_role = constants["ADMIN_ROLE"]
bwcs_role = constants["TOURNEY_ROLE"]

valid_tags = ["QUAL1", "QUAL2", "QUAL3", "QUAL4", "QUAL5", "QUAL6", "QUAL7", "QUAL8"]
cat_map = {
    "POS1": "Placement",
    "POS2": "Placement",
    "POS3": "Placement",
    "POS4": "Placement",
    "POS5": "Placement",
    "POS6": "Placement", 
    "POS1DAY2": "Placement",
    "POS2DAY2": "Placement",
    "POS3DAY2": "Placement",
    "POS4DAY2": "Placement",
    "POS5DAY2": "Placement",
    "POS6DAY2": "Placement",
    "SURV5": "Survival",
    "SURV10": "Survival",
    "SURV15": "Survival",
    "SURV5DAY2": "Survival",
    "SURV10DAY2": "Survival",
    "SURV15DAY2": "Survival",
    "FINAL": "Finals",
    "FINALDAY2": "Finals",
    "BED": "Bed Break",
    "BEDDAY2": "Bed Break",
}
cat_point_map = {
    "POS1": 25,
    "POS2": 18,
    "POS3": 15,
    "POS4": 12,
    "POS5": 10,
    "POS6": 5, 
    "POS1DAY2": 50,
    "POS2DAY2": 36,
    "POS3DAY2": 30,
    "POS4DAY2": 24,
    "POS5DAY2": 20,
    "POS6DAY2": 10,
    "SURV5": 10,
    "SURV10": 5,
    "SURV15": 5,
    "SURV5DAY2": 20,
    "SURV10DAY2": 10,
    "SURV15DAY2": 10,
    "FINAL": 4,
    "FINALDAY2": 8,
    "BED": 7,
    "BEDDAY2": 14,
}

class Tourney(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.teams = json.load(open(teams_file, 'r'))
        self.players = json.load(open(players_file, 'r'))

        self.max_players = max_players_default
        self.max_teams = max_teams_default
        self.curr_id = 0
        self.max_name_len = max_name_len

        self.allowed_channels = allowed_channels
        self.manager_roles = manager_roles
        self.announce_channel = announce_channel
        self.bwcs_role = bwcs_role


    def save_teams(self):
        json.dump(self.teams, open(teams_file, 'w'))

    def save_players(self):
        json.dump(self.players, open(players_file, 'w'))

    def refresh_teams(self):
        self.teams = json.load(open(teams_file, 'r'))
        return self.teams

    def refresh_players(self):
        self.players = json.load(open(players_file, 'r'))
        return self.players

    def is_on_team(self, discord_id):
        discord_id = str(discord_id)
        return discord_id in self.players

    def get_team_name(self, discord_id):
        discord_id = str(discord_id)
        if not self.is_on_team(discord_id):
            return None
        for team in self.teams.values():
            if int(discord_id) in team['members']:
                return team['name']
        return None

    def team_exists(self, team_name):
        return team_name in self.teams

    def get_team(self, discord_id):
        if not self.is_on_team(discord_id):
            return None
        return self.teams[self.get_team_name(discord_id)]

    def create_new_team(self, name, leader):
        self.curr_id += 1
        return {
            'name': name,
            'leader': leader,
            'members': [leader],
            'invites': [],
            'wins': 0,
            'losses': 0,
            'games': [],
            'sign_up_position': len(self.teams),
            'id': self.curr_id
            # each element should be in the format {
            # 'team_1': 'name',
            # 'team_2': 'name',
            # 'winner': 'name',
            # 'team_1_wins': 0,
            # 'team_2_wins': 0
            # }
        }

    def update_teams(self, team_name, team):
        self.teams[team_name] = team
        self.save_teams()

    def parse_users(self, arr):
        string = ""
        for user in arr:
            string += "<@" + str(user) + "> "
        return string

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        return await ctx.message.reply(embed = self.get_embed(f'Error:\n{error}'),
                                       mention_author = False) 

    @commands.command(name = 'create')
    @commands.cooldown(rate = 1, per = 3)
    async def register(self, ctx, *args):
        if self.is_on_team(ctx.author.id):
            return await ctx.message.reply(embed = self.get_embed(f'You cannot create a new team. You are already on the team `{self.get_team_name(ctx.author.id)}`.'),
                                           mention_author = False)

        if len(args) == 0:
            return await ctx.message.reply(embed = self.get_embed(f'You must state a team name.'),
                                           mention_author = False)

        team_name = " ".join(args)
        if len(team_name) > self.max_name_len:
            return await ctx.message.reply(embed = self.get_embed(f'Your team name is too long, the max length is {self.max_name_len} characters.'),
                                           mention_author = False)

        if self.team_exists(team_name):
            return await ctx.message.reply(embed = self.get_embed(f'`{team_name}` is already taken, please choose a different name.'),
                                           mention_author = False)

        if len(self.teams) > self.max_teams:
            await ctx.message.reply(embed = self.get_embed(f'There are already `{self.max_teams}` in the tournament. You have been waitlisted and will be subbed in if another team drops out.'),
                                           mention_author = False)

        self.teams[team_name] = self.create_new_team(team_name, ctx.author.id)
        self.players[str(ctx.author.id)] = team_name
        self.save_teams()
        self.save_players()

        # await self.announce(ctx, f"Team `{team_name}` created by <@{ctx.author.id}>")

        await ctx.author.add_roles(discord.utils.get(ctx.guild.roles, id = self.bwcs_role))

        return await ctx.message.reply(embed = self.get_embed(f'Team `{team_name}` has been created. Use: `{self.bot.prefix}invite <user>` to invite a friend.'),
                                       mention_author = False)

    @commands.command(name = 'invite', aliases = ['add'], usage = 'invite <DiscordID>')
    @commands.cooldown(rate = 3, per = 3)
    async def invite(self, ctx, player: discord.User):
        if not self.is_on_team(ctx.author.id):
            return await ctx.message.reply(embed = self.get_embed(f'You must create a team first. Use `{self.bot.prefix}create <team_name>`.'),
                                           mention_author = False)

        team = self.get_team(ctx.author.id)
        team_name = team['name']
        if team['leader'] != ctx.author.id:
            return await ctx.message.reply(embed = self.get_embed(f'You are not a team leader. Only team leaders can invite players.'),
                                           mention_author = False)

        if player.id in team['invites']:
            return await ctx.message.reply(embed = self.get_embed(f'User has already been invited to `{team_name}`.'),
                                           mention_author = False)

        if player.id in team['members']:
            return await ctx.message.reply(embed = self.get_embed(f'User is already part of `{team_name}`.'),
                                           mention_author = False)

        if len(team['members']) + len(team['invites']) >= self.max_players:
            return await ctx.message.reply(embed = self.get_embed(f'Team is full `({self.max_players} / {self.max_players})`. Make space by either kicking member/s or canceling any pending invite using `{self.bot.prefix}uninvite <user>`.'),
                                           mention_author = False)

        team['invites'].append(player.id)
        self.update_teams(team['name'], team)

        return await ctx.message.reply(embed = self.get_embed(f'<@{player.id}> has been invited to `{team_name}`\n'
                                       f'To accept this invite, they must run `{self.bot.prefix}accept {team_name}`'),
                                       mention_author = False)

    @commands.command(name = 'accept', aliases = ['join'])
    @commands.cooldown(rate = 3, per = 3)
    async def accept(self, ctx, *args):
        if self.is_on_team(ctx.author.id):
            return await ctx.message.reply(embed = self.get_embed(f'You are already on a team. Run {self.bot.prefix}leave {self.get_team_name(ctx.author.id)} to leave your team.'),
                                           mention_author = False)
        team_name = " ".join(args)
        team = self.teams[team_name]
        if ctx.author.id not in team['invites']:
            return await ctx.message.reply(embed = self.get_embed(f'You have not received an invite from `{team_name}`.'),
                                           mention_author = False)

        team['invites'].remove(ctx.author.id)
        team['members'].append(ctx.author.id)
        self.players[str(ctx.author.id)] = team_name
        self.save_players()
        self.update_teams(team_name, team)

        await self.announce(ctx, f"`{team_name}` has entered the tournament (ID: {team['id']}).\nMembers: {self.parse_users(team['members'])}")

        await ctx.author.add_roles(discord.utils.get(ctx.guild.roles, id = self.bwcs_role))

        return await ctx.message.reply(embed = self.get_embed(f'You have successfully joined `{team_name}`'),
                                       mention_author = False)

    @commands.command(name = 'uninvite')
    async def uninvite(self, ctx, player: discord.User):
        if not self.is_on_team(ctx.author.id):
            return await ctx.message.reply(embed = self.get_embed(f'You are not on a team.'),
                                           mention_author = False)

        team = self.get_team(ctx.author.id)
        team_name = team['name']
        if team['leader'] != ctx.author.id:
            return await ctx.message.reply(embed = self.get_embed(f'You are not a team leader. Only team leaders can uninvite players.'),
                                           mention_author = False)

        if player.id not in team['invites']:
            return await ctx.message.reply(embed = self.get_embed(f'User has not been invited to `{team_name}`.'),
                                           mention_author = False)

        team['invites'].remove(player.id)
        self.update_teams(team['name'], team)

        return await ctx.message.reply(embed = self.get_embed(f'<@{player.id}> has been uninvited from `{team_name}`.'),
                                       mention_author = False)

    @commands.command(name = 'reject')
    async def reject(self, ctx, *args):
        team_name = " ".join(args)
        team = self.teams[team_name]
        if ctx.author.id not in team['invites']:
            return await ctx.message.reply(embed = self.get_embed(f'You have not received an invite from `{team_name}`.'),
                                           mention_author = False)

        team['invites'].remove(ctx.author.id)
        self.update_teams(team['name'], team)

        return await ctx.message.reply(embed = self.get_embed(f'You have rejected `{team_name}`\'is invite.'),
                                       mention_author = False)

    @commands.command(name = 'leave', usage = 'leave <team_name>')
    @commands.cooldown(rate = 3, per = 3)
    async def leave(self, ctx, *args):
        if not self.is_on_team(ctx.author.id):
            return await ctx.message.reply(embed = self.get_embed(f'You are not on a team.'),
                                           mention_author = False)
        team_name = " ".join(args)
        team = self.teams[team_name]

        if team_name == "":
            return await ctx.message.reply(embed = self.get_embed(f'To confirm, state the name of your team by running `{self.bot.prefix}leave <team_name>`'))

        if ctx.author.id not in team['members']:
            return await ctx.message.reply(embed = self.get_embed(f'You are not in `{team_name}`.'),
                                           mention_author = False)

        if team['leader'] == ctx.author.id:
            return await ctx.message.reply(embed = self.get_embed(f'You must use `{self.bot.prefix}disband <team_name>` instead.'),
                                           mention_author = False)

        team['members'].remove(ctx.author.id)
        self.players.pop(str(ctx.author.id))
        self.save_players()
        self.update_teams(team_name, team)

        # await self.announce(ctx, f"<@{ctx.author.id}> left `{team_name}`")

        return await ctx.message.reply(embed = self.get_embed(f'You have successfully left `{team_name}`'),
                                       mention_author = False)

    @commands.command(name = 'disband', aliases = ['abandon'], usage = 'disband <team_name>')
    async def disband(self, ctx, *args):
        if not self.is_on_team(ctx.author.id):
            return await ctx.message.reply(embed = self.get_embed(f'You are not on a team.'),
                                           mention_author = False)

        arg_name = " ".join(args)

        team = self.get_team(ctx.author.id)
        team_name = team['name']

        if arg_name != team_name:
            return await ctx.message.reply(embed = self.get_embed(f'You are not the leader of team `{arg_name}`.'),
                                           mention_author = False)
        
        if team['leader'] != ctx.author.id:
            return await ctx.message.reply(embed = self.get_embed(f'You are not a team leader. Only team leaders can disband the team'),
                                           mention_author = False)    
        if arg_name == "":
            return await ctx.message.reply(embed = self.get_embed(f'To confirm, state the name of your team by running `{self.bot.prefix}disband <team_name>`'))

        for member in team['members']:
            self.players.pop(str(member))

        for team_2 in self.teams.values():
            if team_2['sign_up_position'] > team['sign_up_position']:
                team_2['sign_up_position'] -= 1
                self.teams[team_2['name']] = team_2

        self.teams.pop(team_name)
        self.save_teams()
        self.save_players()

        # No longer needed
        # await self.announce(ctx, f"`{team_name}` has been disbanded by <@{ctx.author.id}>")

        return await ctx.message.reply(embed = self.get_embed(f'You have successfully disbanded `{team_name}`.'),
                                       mention_author = False)

    @commands.command(name = 'kick', aliases = ['remove'], usage = 'kick <DiscordID>')
    @commands.cooldown(rate = 3, per = 3)
    async def kick(self, ctx, player: discord.User):
        if not self.is_on_team(ctx.author.id):
            return await ctx.message.reply(embed = self.get_embed(f'You are not on a team.'), mention_author = False)

        team = self.get_team(ctx.author.id)
        team_name = team['name']
        if team['leader'] != ctx.author.id:
            return await ctx.message.reply(embed = self.get_embed(f'You are not a team leader. Only team leaders can kick players.'),
                                           mention_author = False)
        
        if player.id == team['leader']:
            return await ctx.message.reply(embed = self.get_embed(f'The team leader cannot be kicked.'),
                                           mention_author = False)

        if player.id not in team['members']:
            return await ctx.message.reply(embed = self.get_embed(f'User is not in `{team_name}`.'),
                                           mention_author = False)

        team['members'].remove(player.id)
        self.update_teams(team['name'], team)
        self.players.pop(str(player.id))
        self.save_players()

        await self.announce(ctx, f"`{team_name}` has been removed from the tourney due to lack of players")

        return await ctx.message.reply(embed = self.get_embed(f'<@{player.id}> has been kicked from `{team_name}`'),
                                       mention_author = False)

    @commands.command(name = 'info', aliases = ['i'])
    async def info(self, ctx, player: discord.User):
        if not self.is_on_team(player.id):
            return await ctx.message.reply(embed = self.get_embed(f'User is not on a team.'),
                                           mention_author = False)

        return await ctx.message.reply(embed = self.info_embed(self.get_team(player.id)),
                                       mention_author = False)

    @commands.command(name = 'getteam', aliases = ['team'])
    async def team(self, ctx, *args):
        team_name = " ".join(args)
        if not team_name in self.teams.keys():
            return await ctx.message.reply(embed = self.get_embed(f'Team does not exist.'),
                                           mention_author = False)

        return await ctx.message.reply(embed = self.info_embed(self.teams[team_name]),
                                       mention_author = False) 

    def info_embed(self, team):
        string = ''
        string += f'Name: {team["name"]}, ID: {team["id"]}\n'
        string += f'Wins: {team["wins"]}\n'
        string += f'Losses: {team["losses"]}\n'
        string += f'Members: {self.parse_users(team["members"])}\n'
        string += f'Invites: {self.parse_users(team["invites"])}\n'
        string += f'Sign Up Position: {team["sign_up_position"]}\n'
        return self.get_embed(string)

    @commands.command(name = 'setmaxplayers')
    async def set_max_players(self, ctx, max_players):
        if not any([discord.utils.get(ctx.guild.roles, id = x) in ctx.author.roles for x in self.manager_roles]):
            return await ctx.message.reply(embed = self.get_embed(f'You are not a manager. Only managers can set max players.'),
                                           mention_author = False)

        max_players = int(max_players)
        self.max_players = max_players
        return await ctx.message.reply(embed = self.get_embed(f'Max players set to {self.max_players}.'),
                                       mention_author = False)

    @commands.command(name = 'setmaxteams')
    async def set_max_teams(self, ctx, max_teams):
        if not any([discord.utils.get(ctx.guild.roles, id = x) in ctx.author.roles for x in self.manager_roles]):
            return await ctx.message.reply(embed = self.get_embed(f'You are not a manager. Only managers can set max teams.'),
                                           mention_author = False)

        max_teams = int(max_teams)
        self.max_teams = max_teams
        return await ctx.message.reply(embed = self.get_embed(f'Max teams set to {self.max_teams}.'),
                                       mention_author = False)

    @commands.command(name = 'cleargames')
    async def clear_games(self, ctx):
        if not any([discord.utils.get(ctx.guild.roles, id = x) in ctx.author.roles for x in self.manager_roles]):
            return await ctx.message.reply(embed = self.get_embed(f'You are not a manager. Only managers can clear games.'),
                                           mention_author = False)

        for team in self.teams:
            team['games'] = []
            self.teams[team['name']] = team

        return await ctx.message.reply(embed = self.get_embed(f'Successfully cleared all games.'),
                                       mention_author = False)

    @commands.command(name = 'kickteam')
    async def kick_team(self, ctx, *args):
        if not any([discord.utils.get(ctx.guild.roles, id = x) in ctx.author.roles for x in self.manager_roles]):
            return await ctx.message.reply(embed = self.get_embed(f'You are not a manager. Only managers can kick teams.'),
                                           mention_author = False)

        team_name = " ".join(args)

        if team_name == "":
            return await ctx.message.reply(embed = self.get_embed(f'Please enter the team name: `{self.bot.prefix}kickteam <team_name>`'))


        if team_name not in self.teams.keys():
            return await ctx.message.reply(embed = self.get_embed(f'Team {team_name} does not exist.'),
                                           mention_author = False)

        for team_2 in self.teams.values():
            if team_2['sign_up_position'] > self.teams[team_name]['sign_up_position']:
                team_2['sign_up_position'] -= 1
                self.teams[team_2['name']] = team_2
        for member in self.teams[team_name]['members']:
            self.players.pop(str(member))
        self.teams.pop(team_name)
        self.save_teams()
        self.save_players()

        await self.announce(ctx, f"`{team_name}` has been removed from the tourney by <@{ctx.author.id}>")



        return await ctx.message.reply(embed = self.get_embed(f'Successfully removed team `{team_name}`'),
                                       mention_author = False)

    @commands.command(name = 'score')
    async def add_points(self, ctx, name, tag, category):
        if discord.utils.get(ctx.guild.roles, id=admin_role) is None:
            return await ctx.message.reply(embed = self.get_embed(f'Permission denied.'), mention_author = False)
        
        tag = tag.upper()
        category = category.upper()

        if name not in self.teams:
            return await ctx.message.reply(embed = self.get_embed(f'This team does not exist.'), mention_author = False)
        
        if tag not in valid_tags:
            return await ctx.message.reply(embed = self.get_embed(f'This tag does not exist.'), mention_author = False)
        
        if category not in cat_map:
            return await ctx.message.reply(embed = self.get_embed(f'This category does not exist.'), mention_author = False)
        
        team = self.teams[name]
        points = cat_point_map[category]
        cat = cat_map[category]
        
        return await ctx.message.reply(embed = self.get_embed(f'Team `{team["name"]}` +{points} {cat} points! ({tag})'), mention_author = False)

    async def announce(self, ctx, message):
        channel = discord.utils.get(ctx.guild.channels, id = self.announce_channel)
        return await channel.send(message)

    def get_embed(self, description):
        return discord.Embed(
            description = description,
            color = 0x4b61df,
        ).set_footer(text = "BedWars Championship's Tourney")


    # score game
    # view teams lb

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

        if interaction.guild and any(role.id == admin_role for role in interaction.user.roles):

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
