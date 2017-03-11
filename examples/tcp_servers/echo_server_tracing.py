#!/usr/bin/python

import guild
from guild.actor import *
from guild.network import ServerCore, stop_selector, waitfor_selector

class EchoProtocol(Actor):
    @late_bind_safe
    def output(self, chunk):
        pass

    @actor_method
    def input(self, chunk):
        self.output(chunk)


class EchoServer(ServerCore):
    server_options = { "port" : 1601 }
    protocol_class=EchoProtocol


guild.actor.strace = True
guild.network.debug = True

echo_server = EchoServer()

echo_server.start()

wait_KeyboardInterrupt()

stop(echo_server)

stop_selector()

wait_for(echo_server)
waitfor_selector()
