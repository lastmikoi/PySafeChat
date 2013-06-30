import re
import os.path
import threading
import ConfigParser
import binascii
from Crypto import Random
from Crypto.PublicKey import RSA
from twisted.internet.error import ReactorNotRunning
from twisted.internet import reactor, protocol

DEFAULT_RSA_SIZE = 1024
RNG = 0


def myThread(self):
    while True:
        user_input = raw_input("")
        reactor.callFromThread(self.sendMessage, user_input)


class MyClient(protocol.Protocol):
    def __init__(self, key):
        self.RSAkey = key

    def connectionMade(self):
        self.sendMessage(username)
        t = threading.Thread(target=myThread, args=(self,))
        t.setDaemon(True)
        t.start()
        print 'Connected.'

    def dataReceived(self, data):
        pattern = r'''CHLG:{([^>]+)}'''
        m = re.search(pattern, data)
        if m is not None:
            challenge = m.group(1)
            sig = self.RSAkey.sign(challenge, RNG)
            self.sendMessage("RESP:{%s}" % (sig[0]))
        print data

    def sendMessage(self, msg):
        if msg == "/rsa":
            self.transport.write(self.RSAkey.publickey().exportKey() + '\r\n')
        elif msg == "/bye":
            reactor.stop()
        else:
            self.transport.write(msg + '\r\n')

    def connectionLost(self, reason):
        print "Connection lost"
        try:
            reactor.stop()
        except ReactorNotRunning:
            pass


class MyClientFactory(protocol.ClientFactory):

    def __init__(self, key):
        self.RSAkey = key

    def buildProtocol(self, addr):
        return MyClient(self.RSAkey)


def get_config():
    cfg = ConfigParser.RawConfigParser()
    print cfg.read('cfg.cfg')
    if cfg.read('cfg.cfg') == []:
        with file("cfg.cfg", "wb") as f:
            cfg.add_section('User')
            cfg.add_section('Connection')
            cfg.set('User', 'username', raw_input("Enter your username :"))
            cfg.set('Connection', 'host', raw_input("PySafe server host :"))
            cfg.set('Connection', 'port', raw_input("PySafe server port :"))
            cfg.write(f)
    return cfg


def get_rsa():
    RNG = Random.new().read

    def read_rsa():
        with file("mykey.pem") as f:
            data = f.read()
            try:
                passphrase = raw_input(
                    "Please enter RSA passphrase(none by default) :"
                )
                key = RSA.importKey(data, passphrase)
            except TypeError:
                key = RSA.importKey(data)
            return key

    def gen_rsa():
        key = RSA.generate(DEFAULT_RSA_SIZE, RNG)
        with file("mykey.pem", "w") as f:
            f.write(key.exportKey() + "\n")
            f.write(key.publickey().exportKey())

    while True:
        if os.path.exists(r'./mykey.pem'):
            try:
                key = read_rsa()
                break
            except binascii.Error:
                gen_rsa()
        else:
            gen_rsa()
            try:
                key = read_rsa()
                break
            except binascii.Error:
                pass
    return key

if __name__ == '__main__':
    config = get_config()
    RSAkey = get_rsa()
    username = config.get('User', 'username')
    HOST = config.get('Connection', 'host')
    PORT = config.getint('Connection', 'port')
    factory = MyClientFactory(RSAkey)
    reactor.connectTCP(HOST, PORT, factory)
    reactor.run()
