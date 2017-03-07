#!/usr/bin/python

from guild.actor import *
from guild.network import ServerCore, stop_selector, waitfor_selector


class EchoServer(ServerCore):
    server_options = { "port" : 1602 }
    class protocol_class(Actor):
        @late_bind_safe
        def output(self, chunk):
            pass

        @actor_method
        def input(self, chunk):
            self.output(chunk)


echo_server = EchoServer()

echo_server.start()

wait_KeyboardInterrupt()

stop(echo_server)

stop_selector()

wait_for(echo_server)
waitfor_selector()
