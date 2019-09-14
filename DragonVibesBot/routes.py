from app import app
from Websocket import SoundSocket
from SimpleWebSocketServer import SimpleWebSocketServer
from flask import send_file
#from flask_socketio import send, emit

soundSocket = SimpleWebSocketServer('0.0.0.0', 8765, SoundSocket)

@app.route('/')
@app.route('/index')
def index():
    return 'I am a placeholder. Watch me hold places.'
    
@app.route('/twitchWebhook')
def twitchWebhook():
    return 'I am a placeholder. Watch me hold places.'
    
@app.route('/sounds/reaper')
def soundsReaper():
    soundSocket.sendSound("reaper")
    
@app.route('/sounds/ghost')
def soundsGhost():
    soundSocket.sendSound("ghost")
    
@app.route('/sounds/sea')
def soundsSea():
    soundSocket.sendSound("sea")
    
@app.route('/sounds/teleporter')
def soundsTeleporter():
    soundSocket.sendSound("teleporter")
    
@app.route('/sounds/roar')
def soundsRoar():
    soundSocket.sendSound("roar")
    
@app.route('/audio/reaper')
def audioReaper():
    return send_file("audio/reaper.mp3", mimetype="audio/mpeg", as_attachment=True, attachment_filename="reaper.mp3")
    
#@socketio.on('message')
#def handle_message(message):
#    print('received message: ' + message)