from DragonVibesBot import app
from .Websocket import SoundSocket
from SimpleWebSocketServer import SimpleWebSocketServer
from flask import send_file, render_template
import os
import signal
import threading

soundSocket = SimpleWebSocketServer('0.0.0.0', 8765, SoundSocket)
socketThread = threading.Thread(target=soundSocket.serveforever)
socketThread.start()

reapThread = None
ghostThread = None
seaThread = None
teleporterThread = None
roarThread = None

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')
    
@app.route('/toggleOnOff', methods = ['GET', 'POST'])
def toggle():
    print("Toggle the bot!")
    if os.path.isfile("/tmp/dragonvibesbot.pid"):
        with open("/tmp/dragonvibesbot.pid", 'r') as tmpFile:
            pid = tmpFile.read()
            os.kill(int(pid), signal.SIGTERM)
    else:
        os.system('gnome-terminal -x python3 Bot/Bot.py')
    return render_template('index.html', title='Home')
    
@app.route('/twitchWebhook')
def twitchWebhook():
    return 'I am a placeholder. Watch me hold places.'
    
@app.route('/sounds/reaper')
def soundsReaper():
    reapThread = threading.Thread(target=SoundSocket.sendSound, args=(soundSocket.websocketclass, "reaper", ))
    reapThread.start()
    
@app.route('/sounds/ghost')
def soundsGhost():
    ghostThread = threading.Thread(target=SoundSocket.sendSound, args=(soundSocket.websocketclass, "ghost", ))
    ghostThread.start()
    
@app.route('/sounds/sea')
def soundsSea():
    seaThread = threading.Thread(target=SoundSocket.sendSound, args=(soundSocket.websocketclass, "sea", ))
    seaThread.start()
    
@app.route('/sounds/teleporter')
def soundsTeleporter():
    teleporterThread = threading.Thread(target=SoundSocket.sendSound, args=(soundSocket.websocketclass, "teleporter", ))
    teleporterThread.start()
    
@app.route('/sounds/roar')
def soundsRoar():
    roarThread = threading.Thread(target=SoundSocket.sendSound, args=(soundSocket.websocketclass, "roar", ))
    roarThread.start()
    
@app.route('/audio/reaper')
def audioReaper():
    return send_file("audio/reaper.mp3", mimetype="audio/mpeg", as_attachment=True, attachment_filename="reaper.mp3")
    
@app.route('/audio/ghost')
def audioGhost():
    return send_file("audio/ghost.mp3", mimetype="audio/mpeg", as_attachment=True, attachment_filename="ghost.mp3")
    
@app.route('/audio/sea')
def audioSea():
    return send_file("audio/sea.mp3", mimetype="audio/mpeg", as_attachment=True, attachment_filename="sea.mp3")
    
@app.route('/audio/teleporter')
def audioTeleporter():
    return send_file("audio/teleporter.mp3", mimetype="audio/mpeg", as_attachment=True, attachment_filename="teleporter.mp3")
    
@app.route('/audio/roar')
def audioRoar():
    return send_file("audio/roar.mp3", mimetype="audio/mpeg", as_attachment=True, attachment_filename="roar.mp3")