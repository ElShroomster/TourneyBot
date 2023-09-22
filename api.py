import requests
import urllib.parse
import json
import aiohttp

class APIError(Exception):
    pass

def raiseIfError(data):
    if "success" in data:
        if not data["success"]:
            message = data["message"]
            raise APIError(message)
        elif "data" in data:
            return data["data"]
    
    return data

class API:

    def __init__(self, session):
        self.session: aiohttp.ClientSession = session

    async def get(self,path):
        async with self.session.get(path) as res:
            return raiseIfError(await res.json())

    async def post(self,path, body, requesterId):
        body["requesterId"] = str(requesterId)

        async with self.session.post(path, json=body) as res:
            return raiseIfError(await res.json())


    async def getStatus(self):
        res = await self.get("/")
        return "running" in res

    async def getTeams(self):
        return await self.get("/teams")

    async def getUserTeam(self, requester):
        return await self.post("/teams/me", {}, requester)

    async def getTeam(self,name):
        name = urllib.parse.quote(name, safe='')
        return await self.get(f'/teams/{name}')

    async def getTeamMembers(self, name):
        name = urllib.parse.quote(name, safe='')
        return await self.get(f'/teams/{name}/members')

    async def getTeamPending(self, name):
        name = urllib.parse.quote(name, safe='')
        return await self.get(f'/teams/{name}/pending')

    async def createTeam(self, name, requester):
        return await self.post(f'/teams', {
            "name": name,
        }, requester)

    async def forceDisband(self, name, requester):
        name = urllib.parse.quote(name, safe='')
        return await self.post(f'/teams/{name}/forcedisband', {}, requester)

    async def disbandTeam(self, name, requester):
        name = urllib.parse.quote(name, safe='')
        return await self.post(f'/teams/{name}/disband', {}, requester)

    async def inviteToTeam(self, user, requester):
        return await self.post(f'/teams/invite', {
            "userId": str(user),
        }, requester)

    async def acceptInvite(self, name, requester):
        name = urllib.parse.quote(name, safe='')
        return await self.post(f'/teams/{name}/accept', {}, requester)

    async def rejectInvite(self, name, requester):
        name = urllib.parse.quote(name, safe='')
        return await self.post(f'/teams/{name}/reject', {}, requester)

    async def withdrawInvite(self, user, requester):
        return await self.post(f'/teams/withdraw', {
            "userId": str(user)
        }, requester)

    async def kickMember(self, user, requester):
        return await self.post(f'/teams/kick', {
            "userId": str(user)
        }, requester)

    async def leaveTeam(self, name, requester):
        return await self.post(f'/teams/{name}/leave', {}, requester)

    async def scorePos(self, name, bracket, quantity):
        name = urllib.parse.quote(name, safe='')
        return await self.post(f'/teams/{name}/pos', {
            "quantity": int(quantity),
            "bracket": bracket
        }, "")

    async def scoreTime(self, name, bracket, quantity):
        name = urllib.parse.quote(name, safe='')
        return await self.post(f'/teams/{name}/time', {
            "quantity": int(quantity),
            "bracket": bracket
        }, "")

    async def scoreFinals(self, name, bracket, quantity):
        name = urllib.parse.quote(name, safe='')
        return await self.post(f'/teams/{name}/finals', {
            "quantity": int(quantity),
            "bracket": bracket
        }, "")

    async def scoreBeds(self, name, bracket, quantity):
        name = urllib.parse.quote(name, safe='')
        return await self.post(f'/teams/{name}/beds', {
            "quantity": int(quantity),
            "bracket": bracket
        }, "")

    async def checkScore(self, name, bracket):
        name = urllib.parse.quote(name, safe='')
        return await self.post(f'/teams/{name}/score', {
            "bracket": bracket
        }, "")

    async def getBracketScores(self, bracket):
        return await self.post(f'/teams/score', {
            "bracket": bracket
        }, "")

    async def getBracketStatus(self, bracket):
        return await self.get(f'/brackets/{bracket}')

    async def changeBracketLock(self, bracket, lock):
        return await self.post(f'/brackets/lock', {
            "bracket": bracket,
            "lock": bool(lock)
        }, "")