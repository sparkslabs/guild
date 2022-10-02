#!/usr/bin/python
"""mini-guild Example

Simple network example

"""

import time
import socket
import sys
import select

from miniguild import Scheduler, Actor

class EchoProtocol(Actor):
    class Behaviour:
        def input(self, data):
            print("PH: OUTPUT FUNC", self.output)
            print('PH: received "%s"' % data, file=sys.stderr)
            if data:
                print('PH: sending data back to the client', file=sys.stderr)
                self.output(data)
            else:
                print('PH: no more data from', "self.client_address", file=sys.stderr)
                self.output(None)
                self._wrapper.stop()
    actor_methods = ["input"]

class ConnectionHandler(Actor):
    class Behaviour:
        def __init__(self, connection, remote_address):
            self.connection = connection
            self.remote_address = remote_address
            self.running = True

        def main(self):
            conn = self.connection
            try:
                print('CH: connection from', self.remote_address, file=sys.stderr)
                # Receive the data in small chunks and retransmit it
                while self.running:
                    yield 1
                    r,w,e = select.select([self.connection],[],[], 0.01)  # Is there data to read?
                    if r != []:
                        print("CH: RETRIEVING DATA", self.connection, self.remote_address)
                        data = self.connection.recv(16)
                        self.output(data)   # Send to protocol handler

            finally:
                # Clean up the connection
                self.connection.close()
            print('CH: Connection Handler Shutdown', self.remote_address, file=sys.stderr)


        def input(self, data):
            # Input from the protocol handler
            print("CH: Data from protocol", data)
            if data is None:
                self.running = False
                return
            self.connection.sendall(data)

    actor_methods = ["input"]


class TCPServer(Actor):
    class Behaviour:
        port = 12345
        host = "0.0.0.0"
        Protocol = EchoProtocol

        def main(self):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allow fast reuse of socket
            sock.bind((self.host, self.port))
            sock.listen(1)

            while True:
                yield 1
                # Wait for a connection
                print('TCPS: waiting for a connection', file=sys.stderr)
                connection, client_address = sock.accept()
                ch = ConnectionHandler(connection, client_address)
                ph = self.Protocol()
                # Bidirectional links between protocol and client handlers:
                ph.link("output", ch.input)
                ch.link("output", ph.input)

                ch.background()
                ph.background()




class TCPClient(Actor):
    class Behaviour:
        def __init__(self, host, port, ph):
            self.host = host
            self.port = port
            self.ph = ph

        def main(self):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (self.host, self.port)
            print('TCPC: connecting to %s port %s' % server_address, file=sys.stderr)
            sock.connect(server_address)

            ch = ConnectionHandler(sock, server_address)
            self.ph.link("output", ch.input)
            ch.link("output", self.ph.input)

            ch.background()
            self.ph.background()

            yield 1 


class ProducerConsumer(Actor):
    blocking = True
    class Behaviour:
        def __init__(self, message):
            self.message = message
            self.count = 0

        def main(self):
            while True:
                yield 1
                self.output(self.message)
                time.sleep(1)  # So we can see what's happening...

        def input(self, data):
            self.count += 1
            print("********************************************************************")
            print("Munched:", data, self.count)
            print("********************************************************************")
            self.sleeping = True

    actor_methods = ["input"]

if __nme__ == "__main__":
    tcps = TCPServer()
    tcps.background()
    time.sleep(1)

    client_ph = ProducerConsumer(message=b"This is the message to be sent, it will be echoed back")
    tcpc = TCPClient("127.0.0.1", 12345, client_ph)
    tcpc.background()

    while True:
        time.sleep(1)
