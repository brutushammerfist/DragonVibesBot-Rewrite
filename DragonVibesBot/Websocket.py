from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket

class SoundSocket(WebSocket):
    
    clients = []
    
    def handleMessage(self):
        pass
    
    def handleConnected(self):
        print(self.address, 'connected')
        self.clients.append(self)
    
    def handleClose(self):
        print(self.address, 'closed')
        self.clients.remove(self)
    
    def sendSound(self, soundType):
        for client in self.clients:
            client.sendMessage(soundType)