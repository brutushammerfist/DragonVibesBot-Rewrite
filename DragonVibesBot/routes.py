from DragonVibesBot import app
from .Websocket import SoundSocket
from SimpleWebSocketServer import SimpleWebSocketServer
from flask import send_file, render_template
import os
import signal
import threading
import asyncio
#import Bot

import sys
sys.path.insert(0, '..')

from Bot.Bot import Bot

soundSocket = SimpleWebSocketServer('0.0.0.0', 8765, SoundSocket)
socketThread = threading.Thread(target=soundSocket.serveforever)
socketThread.start()

reapThread = None
ghostThread = None
seaThread = None
teleporterThread = None
roarThread = None

botStatus = True

bot = Bot()
botThread = threading.Thread(target=bot.run)
botThread.start()

def handle_async(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

worker_loop = asyncio.new_event_loop()
worker = threading.Thread(target=handle_async, args=(worker_loop, ))
worker.start()

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')
    
@app.route('/toggleOnOff', methods = ['GET', 'POST'])
def toggle():
    print("Toggle the bot!")
    #if os.path.isfile("/tmp/dragonvibesbot.pid"):
    #    with open("/tmp/dragonvibesbot.pid", 'r') as tmpFile:
    #        pid = tmpFile.read()
    #        os.kill(int(pid), signal.SIGTERM)
    #    os.remove("/tmp/dragonvibesbot.pid")
    #else:
    #    os.system('gnome-terminal -x python3 Bot/Bot.py')
    global botStatus

    asyncio.run_coroutine_threadsafe(bot.toggle(botStatus), worker_loop)

    if botStatus:
        botStatus = False
    else:
        botStatus = True

    #bot.toggle()

    return render_template('index.html', title='Home')
    
@app.route('/twitchWebhook')
def twitchWebhook():
    return 'I am a placeholder. Watch me hold places.'
    
@app.route('/sounds/reaper')
def soundsReaper():
    reapThread = threading.Thread(target=SoundSocket.sendSound, args=(soundSocket.websocketclass, "reaper", ))
    reapThread.start()
    return ("OK", 200, )
    
@app.route('/sounds/ghost')
def soundsGhost():
    ghostThread = threading.Thread(target=SoundSocket.sendSound, args=(soundSocket.websocketclass, "ghost", ))
    ghostThread.start()
    return ("OK", 200, )
    
@app.route('/sounds/sea')
def soundsSea():
    seaThread = threading.Thread(target=SoundSocket.sendSound, args=(soundSocket.websocketclass, "sea", ))
    seaThread.start()
    return ("OK", 200, )
    
@app.route('/sounds/teleporter')
def soundsTeleporter():
    teleporterThread = threading.Thread(target=SoundSocket.sendSound, args=(soundSocket.websocketclass, "teleporter", ))
    teleporterThread.start()
    return ("OK", 200, )
    
@app.route('/sounds/roar')
def soundsRoar():
    roarThread = threading.Thread(target=SoundSocket.sendSound, args=(soundSocket.websocketclass, "roar", ))
    roarThread.start()
    return ("OK", 200, )
    
@app.route('/audio/reaper')
def audioReaper():
    return send_file("audio/reaper.mp3", mimetype="audio/mpeg", as_attachment=True, attachment_filename="reaper.mp3")
    
#@app.route('/audio/ghost')
#def audioGhost():
    #return send_file("audio/ghost.mp3", mimetype="audio/mpeg", as_attachment=True, attachment_filename="ghost.mp3")

#@app.route('/audio/sea')
#def audioSea():
    #return send_file("audio/sea.mp3", mimetype="audio/mpeg", as_attachment=True, attachment_filename="sea.mp3")

#@app.route('/audio/teleporter')
#def audioTeleporter():
    #return send_file("audio/teleporter.mp3", mimetype="audio/mpeg", as_attachment=True, attachment_filename="teleporter.mp3")

#@app.route('/audio/roar')
#def audioRoar():
    #return send_file("audio/roar.mp3", mimetype="audio/mpeg", as_attachment=True, attachment_filename="roar.mp3")
