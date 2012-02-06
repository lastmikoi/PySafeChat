from twisted.internet import reactor, protocol, threads
from sys import stdout
from Crypto.PublicKey import RSA
from Crypto import Random
import time
import threading
import re

HOST = 'localhost'
PORT = 4150

def myThread(self):
  while 1:
    time.sleep(1)
    reactor.callFromThread(self.sendMessage,raw_input(""))
    pass

class MyClient(protocol.Protocol):
  def __init__(self, RSAkey):
    self.RSAkey = RSAkey

  def connectionMade(self):
    t = threading.Thread(target=myThread, args=(self,))
    t.setDaemon(True)
    t.start()
    self.sendMessage("lastmikoi")
    print 'Connected.'

  def dataReceived(self, data):
    pattern=r'''CHLG:{([^>]+)}'''
    m = re.search(pattern, data)
    if m is not None:
      challenge = m.group(1)
      sig = self.RSAkey.sign(challenge, rng)
      sig = sig[0]
      self.sendMessage("RESP:{%s}" % (sig))
    stdout.write("\t" + data)

  def sendMessage(self, msg):
    if msg == "/rsa":
      self.transport.write(self.RSAkey.publickey().exportKey()+'\r\n')
    elif msg == "/bye":
      reactor.stop()
    else:
      self.transport.write(msg + '\r\n')
  pass

  def connectionLost(self, reason):
    print "Connection lost"
    try:
      reactor.stop()
    except Exception:
      pass

class MyClientFactory(protocol.ClientFactory):
  def __init__(self, RSAkey):
    self.RSAkey = RSAkey

  def buildProtocol(self, addr):
    return MyClient(self.RSAkey)
  pass

global rng
if __name__ == '__main__':
  RSAkey = None
  rng = Random.new().read
  try:
    with file("mykey.pem") as f:
      RSAkey = RSA.importKey(f.read(), raw_input("Please enter RSA passphrase(none by default) :"))
  except IOError:
    RSAkey = RSA.generate(1024, rng)
    with file("mykey.pem", "w") as f:
      f.write(RSAkey.exportKey()+"\n")
      f.write(RSAkey.publickey().exportKey())
  factory = MyClientFactory(RSAkey)
  reactor.connectTCP(HOST, PORT, factory)
  reactor.run()
