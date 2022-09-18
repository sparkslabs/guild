#!/usr/bin/python
"""mini-guild Example

Simple network example

"""

import socket
import sys
import select

from miniguild import Scheduler, Actor

class Protocol(Actor):
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
        def __init__(self, connection, client_address):
            self.connection = connection
            self.client_address = client_address
            self.running = True

        def main(self):
            conn = self.connection
            proto = Protocol()
            try:
                print('CH: connection from', self.client_address, file=sys.stderr)
                # Receive the data in small chunks and retransmit it
                while self.running:
                    yield 1
                    r,w,e = select.select([self.connection],[],[], 0.01)  # Is there data to read?
                    if r != []:
                        print("CH: WAITING FOR DATA", self.connection, self.client_address)
                        data = self.connection.recv(16)
                        self.output(data)   # Send to protocol handler

            finally:
                # Clean up the connection
                self.connection.close()
            print('CH: Connection Handler Shutdown', self.client_address, file=sys.stderr)


        def input(self, data):
            # Input from the protocol handler
            print("DATA FROM PROTOCOL", data)
            if data is None:
                self.running = False
                return
            self.connection.sendall(data)

    actor_methods = ["input"]


class TCPServer:
    port = 12345
    host = "0.0.0.0"

    def main(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allow fast reuse of socket
        sock.bind((self.host, self.port))
        sock.listen(1)

        while True:
            # Wait for a connection
            print('waiting for a connection', file=sys.stderr)
            connection, client_address = sock.accept()
            ch = ConnectionHandler(connection, client_address)
            ph = Protocol()
            # Bidirectional links between protocol and client handlers:
            ph.link("output", ch.input)
            ch.link("output", ph.input)

            ch.background()
            ph.background()


tcps = TCPServer()
tcps.main()
