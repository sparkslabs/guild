#!/usr/bin/python
"""mini-guild Example

Simple network example

"""

import socket
import sys

from miniguild import Scheduler, Actor

class Protocol:
    def __init__(self, output):
        self.output = output

    def input(self, data):
        print('received "%s"' % data, file=sys.stderr)
        if data:
            print('sending data back to the client', file=sys.stderr)
            self.output(data)
        else:
            print('no more data from', "self.client_address", file=sys.stderr)
            self.output(None)


class ConnectionHandler(Actor):
    class Behaviour:
        def __init__(self, connection, client_address):
            self.connection = connection
            self.client_address = client_address
            self.running = True

        def main(self):
            proto = Protocol(self.output)
            try:
                print('connection from', self.client_address, file=sys.stderr)
                # Receive the data in small chunks and retransmit it
                while self.running:
                    yield 1
                    data = self.connection.recv(16)
                    proto.input(data)
                    
            finally:
                # Clean up the connection
                self.connection.close()
            print('Connection Handler Shutdown', self.client_address, file=sys.stderr)

        def output(self, data):
            if data is None:
                self.running = False
                return
            self.connection.sendall(data)

    

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
            ch.background()



tcps = TCPServer()
tcps.main()
