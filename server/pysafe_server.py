from twisted import *
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Factory
from Crypto.PublicKey import RSA
import authing
import re

class	Chat(LineReceiver):
  def __init__(self, users):
    self.users = users
    self.name = None
    self.state = "GETNAME"
    from Crypto.Hash import MD5
    from Crypto.Random.random import getrandbits
    self.myhash = MD5.new()
    self.myhash.update(str(getrandbits(42)))
    self.challenge = self.myhash.hexdigest()

  def connectionMade(self):
    self.sendLine("Welcome to mikoi's pychat\nPlease enter your username")
    print "Connected %s" % (self.transport.getPeer())

  def connectionLost(self, reason):
    if self.name is not "":
      self.broadcast("#PART>", True)
      for name, protocol in self.users.iteritems():
	if name == self.name:
	  self.users.pop(name)
	  break
      print "Lost %s" % (self.name)

  def is_online(self):
    for name, protocol in self.users.iteritems():
      if protocol != self:
	if name == self.name:
	  return True
    return False

  def lineReceived(self, line):
    if self.state == "GETNAME":
      self.name = line
      if self.is_online() is True:
	self.message("User %s already online, disconnecting." % (self.name))
	self.name = ""
	self.transport.loseConnection()
	return
      auth = authing.get_auth(self.name)
      if auth == 'Unknown':
	self.state = "NEWUSER"
	self.message("User %s not found, registering a new one.\n"\
		     "Please send your RSA public key." % (self.name))
      elif auth == 'Ok':
	self.state = "AUTHING"
	self.message("User found, please sign and return the challenge\n"\
		     "CHLG:{%s}" % (self.challenge))
    elif self.state == "NEWUSER":
      self.user_pubkey = RSA.importKey(line).publickey().exportKey()
      authing.add_user(self.name, self.user_pubkey)
      self.state = "AUTHING"
      self.message("New user sucessfully created, please sign and return the challenge\n"\
		     "CHLG:{%s}" % (self.challenge))
    elif self.state == "AUTHING":
      self.user_pubkey = RSA.importKey(authing.get_pubkey(self.name))
      pattern=r'''RESP:{([^>]+)}'''
      m = re.search(pattern, line)
      if m is not None:
	if self.user_pubkey.verify(self.challenge, (long(m.group(1)),)):
	  self.message("Authed succesfully, welcome back %s !" % (self.name))
	  self.users[self.name] = self
	  print "%s authed." % (self.name)
	  self.broadcast("#JOIN>", True)
	  self.state = "OK"
	else:
	  self.message("Auth failed, please try again:\n"\
		     "CHLG:{%s}" % (self.challenge))
    elif self.state == "OK":
      print "Transmitted from", self.name, ':', line
      self.broadcast(line, False)

  def broadcast(self, message, is_sys):
    for name, protocol in self.users.iteritems():
      if protocol != self:
	if is_sys:
	  protocol.sendLine('SYST> '+str(self.name) + ' --- '+str(message))
	else:
	  protocol.sendLine(self.name+':'+message)

  def message(self, message):
    self.transport.write(message + "\n")

class myFactory(Factory):

  def __init__(self):
    self.users = {}

  def buildProtocol(self, addr):
    return Chat(self.users)

authing.init_db()
reactor.listenTCP(4150, myFactory())
reactor.run()
