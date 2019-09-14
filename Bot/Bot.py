from apscheduler.schedulers.asyncio import AsyncIOScheduler
from random import randrange
from twitchio.ext import commands
from twitchio import *
import os
import json
import requests
import asyncio

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
    secrets = readJson("resources/secrets.json")
    
    # List of current channel mods
    modList = ['DracoAsier', 'BrutusHammerfist']
    
    def __init__(self):
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
        if os.stat("resources/blacklist.csv") is not 0:
            with open("resources/blacklist.csv") as blacklistFile:
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
            commands = self.readJson("resources/commands.json")
            cmd = (message.content[1:].split(" ", 1))[0]
            
            if cmd in commands:
                try:
                    ctx = await self.get_context(message)
                except:
                    pass
                await ctx.send(commands[cmd])
        
        await self.handle_commands(message)
        
    def distributeTokens(self):
        viewerTypes = ['vips', 'moderators', 'staff', 'admins', 'global_mods', 'viewers']
        chatters = requests.get('https://tmi.twitch.tv/group/user/dracoasier/chatters').json()
        checkOnline = requests.get(f'https://api.twitch.tv/helix/streams?user_login=DracoAsier', headers={'Client-ID' : f'{self.twitchClientID}'})
        bank = self.readJson("resources/bank.json")
        
        def checkAndDist(bank, checkOnline, viewerType):
            for viewer in chatters['chatters'][viewerType]:
                if len(checkOnline['data']) != 0:
                    if viewer in bank:
                        bank[viewer] +=1
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
    
    def readJson(self, filename):
        if os.stat(filename) is not 0:
            with open(filename, "r") as jsonfile:
                return json.load(jsonfile)
        
    def writeJson(self, filename, info):
        with open(filename, "w") as jsonfile:
            json.dump(info, jsonfile)
    
    @commands.command(name='test')
    async def testCommand(self, ctx):
        await ctx.send(f'Hello {ctx.author.name}!')
    
    #**
    #   Commands to edit/schedule other commands
    #*
    @commands.command(name='addcom')
    async def addCommand(self, ctx):
        commands = self.readJson("resources/commands.json")
        cmd = ctx.content[8:]
        params = cmd.split(" ", 1)
        
        if params[0] in commands:
            await ctx.send(f'This command already exists, please remove and readd it to edit!')
        else:
            commands[params[0]] = params[1]
            self.writeJson("resources/commands.json", commands)
            await ctx.send(f'Command {params[0]} has been created!')
        
    @commands.command(name='delcom')
    async def delCommand(self, ctx):
        commands = self.readJson("resources/commands.json")
        cmd = ctx.content[8:]
        
        if cmd in commands:
            commands.pop(cmd)
            self.writeJson("resources/commands.json", commands)
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
        bank = self.readJson("resources/bank.json")
        if ctx.author.name in bank:
            await ctx.send(f'You have collected {bank[ctx.author.name]} loyalty points!')
        else:
            await ctx.send("You have not begun collecting loyalty points. Hang out in the stream to do so!")
        
    @commands.command(name='givecoins')
    async def giveCoinsCommand(self, ctx):
        bank = self.readJson("resources/bank.json")
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
            bank = self.readJson("resources/bank.json")
            if ctx.author.name in bank:
                if bank[ctx.author.name] >= self.gaPrice:
                    bank[ctx.author.name] -= self.gaPrice
                    self.gaPool.append(ctx.author.name)
                    self.writeJson("resources/bank.json", bank)
        
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
        pass
        
    @commands.command(name='ghost')
    async def ghostCommand(self, ctx):
        pass
        
    @commands.command(name='sea')
    async def seaCommand(self, ctx):
        pass
        
    @commands.command(name='teleporter')
    async def teleporterCommand(self, ctx):
        pass
        
    @commands.command(name='roar')
    async def roarCommand(self, ctx):
        pass
    
    #**
    #   Misc. Commands
    #*
    @commands.command(name='uptime')
    async def uptimeCommand(self, ctx):
        pass
    
    @commands.command(name='youtube')
    async def youtubeCommand(self, ctx):
        pass
        
    @commands.command(name='tweet')
    async def tweetCommand(self, ctx):
        pass
        
        
    #**
    #   These could really be in the user-defined cmd json file.
    #*
    @commands.command(name='prime')
    async def primeCommand(self, ctx):
        pass
        
    @commands.command(name='artist')
    async def artistCommand(self, ctx):
        pass

try:
    print("Bot starting...")
    bot = Bot()
    bot.run()
except:
    pass
finally:
    os.remove("/tmp/dragonvibesbot.pid")