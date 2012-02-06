from twisted.internet import reactor
from twisted.internet.protocol import Factory
from networking.Chat import *
from authing import init_db

class myFactory(Factory):

  def __init__(self):
    self.users = {}

  def buildProtocol(self, addr):
    return Chat(self.users)

init_db()
reactor.listenTCP(4150, myFactory())
reactor.run()
