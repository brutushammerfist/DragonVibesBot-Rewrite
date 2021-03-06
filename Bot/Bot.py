from apscheduler.schedulers.asyncio import AsyncIOScheduler
from random import randrange
from twitchio.ext import commands
from twitchio import *
from bs4 import BeautifulSoup
import datetime
import os
import json
import requests
import twitter
import asyncio
import time
import threading
import socket

r = requests.get("http://whatismyip.org")

soup = BeautifulSoup(r.content, 'html.parser')

curr_ip = "0.0.0.0"

for link in soup.find_all('a'):
    if link.get('href') == '/my-ip-address':
        curr_ip = link.getText()

print(curr_ip)

class Bot(commands.Bot):
    # Variables used for scheduling commands to run on certain intervals
    scheduler = AsyncIOScheduler()
    #cmds = {
    #    'prime' : primeCommand._callback,
    #    'uptime' : uptimeCommand._callback,
    #    'artist' : artistCommand._callback,
    #    'tweet' : tweetCommand._callback
    #}
    
    # Variable used to tell if the loyalty bank is "open"
    bankOpen = 0
    
    # Lists to hold current entrants for raffles and if they are open
    gaPool = []
    pool = []
    poolOpen = False
    gaOpen = False
    gaPrice = 0
    
    # Dictionary holding all the "secrets"
    secrets = []
    
    # List of current channel mods
    modList = ['DracoAsier', 'BrutusHammerfist']
    
    tweetAPI = None
    
    def __init__(self):
        self.secrets = self.readJson("Bot/resources/secrets.json")
        
        self.tweetAPI = twitter.Api(consumer_key=self.secrets['tweetConsumerKey'],
            consumer_secret=self.secrets['tweetConsumerSecret'],
            access_token_key=self.secrets['tweetAccessTokenKey'],
            access_token_secret=self.secrets['tweetAccessTokenSecret']
        )
        
        # Connect to twitch
        super().__init__(irc_token=self.secrets['twitchIRCToken'], client_id=self.secrets['twitchClientID'], nick='DragonVibesBot', prefix='!', initial_channels=['DracoAsier'])
        
        # Store process id to kill later
        with open("/tmp/dragonvibesbot.pid", "w") as pidFile:
            pidFile.write(str(os.getpid()))
            
        # Start loyalty point distribution schedule
        self.scheduler.add_job(self.distributeTokens, 'interval', seconds=900.0)
        
    async def event_ready(self):
        print(f'Ready | {self.nick}')
        
    async def event_message(self, message):
        print(message.author.name + " : " + message.content)
        
        #Check message for blacklisted words
        if os.stat("Bot/resources/blacklist.csv") is not 0:
            with open("Bot/resources/blacklist.csv") as blacklistFile:
                blacklist = blacklistFile.read()
            for word in blacklist:
                if word in message.content.split(" "):
                    try:
                        ctx = await self.get_context(message)
                    except:
                        pass
                    await ctx.timeout(message.author.name, 1, "Your message contained a blacklisted word!")
                    
        #Check if command is user defined or not
        if message.content[0] is '!':
            commands = self.readJson("Bot/resources/commands.json")
            cmd = (message.content[1:].split(" ", 1))[0]
            
            if cmd in commands:
                try:
                    ctx = await self.get_context(message)
                except:
                    pass
                await ctx.send(commands[cmd])
        
        await self.handle_commands(message)
    
    def readJson(self, filename):
        if os.stat(filename) is not 0:
            with open(filename, "r") as jsonfile:
                return json.load(jsonfile)
        else:
            return ""
        
    def writeJson(self, filename, info):
        with open(filename, "w") as jsonfile:
            json.dump(info, jsonfile)
        
    def distributeTokens(self):
        viewerTypes = ['vips', 'moderators', 'staff', 'admins', 'global_mods', 'viewers']
        chatters = requests.get('https://tmi.twitch.tv/group/user/dracoasier/chatters').json()
        checkOnline = requests.get(f'https://api.twitch.tv/helix/streams?user_login=DracoAsier', headers={'Client-ID' : f'{self.twitchClientID}'})
        bank = self.readJson("Bot/resources/bank.json")
        
        def checkAndDist(bank, checkOnline, viewerType):
            for viewer in chatters['chatters'][viewerType]:
                if len(checkOnline['data']) != 0:
                    if viewer in bank:
                        bank[viewer] += 1
                    else:
                        bank[viewer] = 1
                else:
                    if self.bankOpen == 3:
                        if viewer in bank:
                            bank[viewer] += 1
                        else:
                            bank[viewer] = 1
                        self.bankOpen = 0
                    else:
                        self.bankOpen += 1
        
        for viewerType in viewerTypes:
            checkAndDist(bank, checkOnline, viewerType)
    
    @commands.command(name='test')
    async def testCommand(self, ctx):
        await ctx.send(f'Hello {ctx.author.name}!')
    
    #**
    #   Commands to edit/schedule other commands
    #*
    @commands.command(name='addcom')
    async def addCommand(self, ctx):
        commands = self.readJson("Bot/resources/commands.json")
        cmd = ctx.content[8:]
        params = cmd.split(" ", 1)
        
        if params[0] in commands:
            await ctx.send(f'This command already exists, please remove and readd it to edit!')
        else:
            commands[params[0]] = params[1]
            self.writeJson("Botresources/commands.json", commands)
            await ctx.send(f'Command {params[0]} has been created!')
        
    @commands.command(name='delcom')
    async def delCommand(self, ctx):
        commands = self.readJson("Bot/resources/commands.json")
        cmd = ctx.content[8:]
        
        if cmd in commands:
            commands.pop(cmd)
            self.writeJson("Bot/resources/commands.json", commands)
            await ctx.send(f'Command {cmd} has been removed!')
        else:
            await ctx.send(f'There is no command by that name, try again.')
        
    @commands.command(name='comschedule')
    async def schedCommand(self, ctx):
        params = ctx.content[13:].split(" ")
        
        if params[1] == "stop":
            self.scheduler.remove_job(params[0])
        elif params[1] == "start":
            self.scheduler.add_job(self.cmds[params[0]], 'interval', [self, ctx], seconds=int(params[2]), id=params[0])
    
    #**
    #   Loyalty System Commands
    #*
    @commands.command(name='coins')
    async def coinsCommand(self, ctx):
        bank = self.readJson("Bot/resources/bank.json")
        if ctx.author.name in bank:
            await ctx.send(f'You have collected {bank[ctx.author.name]} loyalty points!')
        else:
            await ctx.send("You have not begun collecting loyalty points. Hang out in the stream to do so!")
        
    @commands.command(name='givecoins')
    async def giveCoinsCommand(self, ctx):
        bank = self.readJson("Bot/resources/bank.json")
        params = ctx.content[11:].split(" ")
        
        if params[0] in bank:
            bank[params[0]] += params[1]
        else:
            bank[params[0]] = params[1]
    
    #**
    #   Giveaway Commands
    #*
    @commands.command(name='gastart')
    async def gaStartCommand(self, ctx):
        params = ctx.content[9:]
        self.gaPrice = int(params)
        self.gaOpen = True
        
        ctx.send(f'Giveaway has been opened! Price for entry is {int(params)} points! Type !gaenter to enter!')
        
    @commands.command(name='gaend')
    async def gaEndCommand(self, ctx):
        self.gaPool.clear()
        self.gaPrice = 0
        self.gaOpen = False
        
        ctx.send(f'Giveaway has concluded!')
        
    @commands.command(name='gaenter')
    async def gaEnterCommand(self, ctx):
        if ctx.author.name in self.gaPool:
            pass
        else:
            bank = self.readJson("Bot/resources/bank.json")
            if ctx.author.name in bank:
                if bank[ctx.author.name] >= self.gaPrice:
                    bank[ctx.author.name] -= self.gaPrice
                    self.gaPool.append(ctx.author.name)
                    self.writeJson("Bot/resources/bank.json", bank)
        
    @commands.command(name='gapull')
    async def gaPullCommand(self, ctx):
        await ctx.send(f'The winner is... {randrange(0, len(self.gaPool) - 1)}!!')
    
    #**
    #   Viewer pulling commands
    #*
    @commands.command(name='poolstart')
    async def poolStartCommand(self, ctx):
        self.poolOpen = True
        
        await ctx.send("A name pull has started! Type !enter to enter!")
        
    @commands.command(name='poolend')
    async def poolEndCommand(self, ctx):
        self.pool.clear()
        self.poolOpen = False
        
        await ctx.send("Name pull over! Everyone can go home now!")
        
    @commands.command(name='enter')
    async def enterCommand(self, ctx):
        if self.poolOpen == True:    
            if ctx.author.name not in self.pool:
                self.pool.append(ctx.author.name)
        
    @commands.command(name='pull')
    async def pullCommand(self, ctx):
        await ctx.send(f'The winner is... {randrange(0, len(self.pool) - 1)}!!')
    
    #**
    #   Sound Commands
    #*
    @commands.command(name='reaper')
    async def reaperCommand(self, ctx):
        r = requests.get(f"http://{curr_ip}/sounds/reaper")
        
    @commands.command(name='ghost')
    async def ghostCommand(self, ctx):
        r = requests.get(f"http://{curr_ip}/sounds/ghost")
        
    @commands.command(name='sea')
    async def seaCommand(self, ctx):
        r = requests.get(f"http://{curr_ip}/sounds/sea")
        
    @commands.command(name='teleporter')
    async def teleporterCommand(self, ctx):
        r = requests.get(f"http://{curr_ip}/sounds/teleporter")
        
    @commands.command(name='roar')
    async def roarCommand(self, ctx):
        r = requests.get(f"http://{curr_ip}/sounds/roar")
    
    #**
    #   Misc. Commands
    #*
    @commands.command(name='uptime')
    async def uptimeCommand(self, ctx):
        r = requests.get(f'https://api.twitch.tv/helix/streams?user_login=DracoAsier', headers={'Client-ID': str(self.secrets['twitchClientID'])}).json()
        
        if len(r['data']) == 0:
            await ctx.send("Stream is currently offline.")
        else:
            startTime = datetime.datetime.strptime(r['data'][0]['started_at'], '%Y-%m-%dT%H:%M:%SZ')
            currTime = datetime.datetime.now()
            timeLive = str(currTime - startTime).split(':')
            await ctx.send(f'The Dragon has been live for {timeLive[0]} hours {timeLive[1]} minutes {int(float(timeLive[2]))} seconds!')
    
    @commands.command(name='youtube')
    async def youtubeCommand(self, ctx):
        plistName = ctx.content[9:]
        plistURL = "https://www.youtube.com/playlist?list="
        
        r = requests.get(str(self.secrets['ytBaseURL'] + "/search?part=snippet&channelId=" + self.secrets['ytChannelID'] + "&type=playlist&q=" + plistName + "&key=" + self.secrets['ytAPI'])).json()
        print(r)
        plistURL = plistURL + str(r['items'][0]['id']['playlistId'])
        
        await ctx.send(f'Here is the playlist you requested: {plistName} - {plistURL}')
        
    @commands.command(name='tweet')
    async def tweetCommand(self, ctx):
        r = self.tweetAPI.GetUserTimeline(screen_name="DracoAsier", count=20, include_rts=False)[0].AsDict()
        
        await ctx.send(str("Here is a link to DracoAsier\'s latest tweet: " + r['urls'][0]['expanded_url']))
        
    @commands.command(name='dvcannon')
    async def dvCannonCommand(self, ctx):
        params = ctx.content[10:]
        
        if params is not "":
            await ctx.send(f'Locking onto {params}...Cannon loaded, firing in 10 seconds!!')
            time.sleep(10)
            await ctx.send(f'dracoaDV https://i.imgur.com/IU3fBKw.gif FIRE!!')
        else:
            await ctx.send(f'Cannon loaded, firing in 10 seconds!!')
            time.sleep(10)
            await ctx.send(f'dracoaDV https://i.imgur.com/IU3fBKw.gif FIRE!!')

    #On/Off switch to leave and join channel
    async def toggle(self, botStatus):
        if botStatus:
            print(botStatus)
            print("Parting!!")
            await self.part_channels(["DracoAsier"])
        else:
            print(botStatus)
            print("Joining!!")
            await self.join_channels(["DracoAsier"])

    async def join(self):
        await self.join_channels(["DracoAsier"])

    async def part(self):
        await self.part_channels(["DracoAsier"])

    def bruh(self):
        print("BRUH!")

#if __name__ == "__main__":
#    print("Bot starting...")
#    bot = Bot()
#    bot.run()
