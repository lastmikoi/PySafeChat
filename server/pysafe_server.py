from twisted.internet import reactor
from twisted.internet.protocol import Factory
from networking.Chat import Chat
from authing import init_db


class ChatFactory(Factory):

    def __init__(self):
        self.users = {}

    def buildProtocol(self, addr):
        return Chat(self.users)

init_db()
reactor.listenTCP(4150, ChatFactory())
reactor.run()
