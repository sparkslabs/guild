#!/usr/bin/python
# -*- coding: utf-8 -*-
"""\
"""

from guild.actor import Actor, actor_method, process_method, late_bind


import socket
import sys, time
import pprint

class MulticastTransceiver(Actor):
  def __init__(self):
    self.local_addr = "224.0.0.123"   # Multicast address we join
    self.local_port = 5040   # and port
    self.remote_addr = "224.0.0.123" # Multicast address we send to (may be same)
    self.remote_port = 5040 # and port.
    self.tosend = []  ## Not Yet...
    self.sock = None
    super(MulticastTransceiver,self).__init__()

  def process_start(self):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((self.local_addr,self.local_port)) # Receive from server on this port

    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
    status = sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(self.remote_addr) + socket.inet_aton("0.0.0.0"))

    sock.setblocking(0)

    self.sock = sock # Now effectively signifes ready...

  @process_method
  def process(self):
        try:
            data, addr = self.sock.recvfrom(16384)
        except socket.error:
            e = sys.exc_info()[1]
        else:
            message = (addr, data)
            self.output(message, time.time())

        while len(self.tosend)>0:
          try:
              l = self.sock.sendto(self.tosend[0], (self.remote_addr,self.remote_port) );
              del self.tosend[0]
          except socket.error:
              # show
              # break out the loop, since we can't send right now
              e = sys.exc_info()[1]
              break

  @actor_method
  def input(self, data):
    self.tosend.append(data)

  @late_bind
  def output(self, data, timestamp):
      pass

if __name__ == "__main__":
    # No demo code at present
    pass

