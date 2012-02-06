import re
import time
import threading
import ConfigParser
from sys import stdout
from Crypto import Random
from Crypto.PublicKey import RSA
from twisted.internet.error import ReactorNotRunning
from twisted.internet import reactor, protocol, threads

DEFAULT_RSA_SIZE = 1024

def myThread(self):
  while True:
    user_input = raw_input("")
    reactor.callFromThread(self.sendMessage,user_input)

class MyClient(protocol.Protocol):
  def __init__(self, RSAkey):
    self.RSAkey = RSAkey

  def connectionMade(self):
    self.sendMessage(username)
    t = threading.Thread(target=myThread, args=(self,))
    t.setDaemon(True)
    t.start()
    print 'Connected.'

  def dataReceived(self, data):
    pattern=r'''CHLG:{([^>]+)}'''
    m = re.search(pattern, data)
    if m is not None:
      challenge = m.group(1)
      sig = self.RSAkey.sign(challenge, rng)
      self.sendMessage("RESP:{%s}" % (sig[0]))
    print data
  def sendMessage(self, msg):
    if msg == "/rsa":
      self.transport.write(self.RSAkey.publickey().exportKey()+'\r\n')
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

  def __init__(self, RSAkey):
    self.RSAkey = RSAkey

  def buildProtocol(self, addr):
    return MyClient(self.RSAkey)

def get_config():
  config = ConfigParser.RawConfigParser()
  if config.read('config.cfg') == []:
    with file("config.cfg", "wb") as f:
      config.add_section('User')
      config.add_section('Connection')
      config.set('User', 'username', raw_input("Enter your username :"))
      config.set('Connection', 'host', raw_input("PySafe server host :"))
      config.set('Connection', 'port', raw_input("PySafe server port :"))
      config.write(f)
  return config

def get_rsa():
  global rng
  rng = Random.new().read
  try:
    with file("mykey.pem") as f:
      passphrase = raw_input("Please enter RSA passphrase(none by default) :")
      RSAkey = RSA.importKey(f.read(), passphrase)
  except IOError:
    RSAkey = RSA.generate(DEFAULT_RSA_SIZE, rng)
    with file("mykey.pem", "w") as f:
      f.write(RSAkey.exportKey()+"\n")
      f.write(RSAkey.publickey().exportKey())
  return RSAkey

if __name__ == '__main__':
  config = get_config()
  RSAkey = get_rsa()
  username = config.get('User', 'username')
  HOST = config.get('Connection', 'host')
  PORT = config.getint('Connection', 'port')
  factory = MyClientFactory(RSAkey)
  reactor.connectTCP(HOST, PORT, factory)
  reactor.run()
