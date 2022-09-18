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
        def __init__(self, connection, client_address):
            self.connection = connection
            self.client_address = client_address
            self.running = True

        def main(self):
            conn = self.connection
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
        def __init__(self, host, port, message):
            self.host = host
            self.port = port
            self.message = message

        def main(self):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (self.host, self.port)
            print('TCPC: connecting to %s port %s' % server_address, file=sys.stderr)
            sock.connect(server_address)

            try:
                print('TCPC: sending "%s"' % self.message, file=sys.stderr)
                sock.sendall(self.message)

                received = 0
                expected = len(self.message)

                while received < expected:
                    data = sock.recv(16)
                    received += len(data)
                    print('TCPC: received "%s"' % data, file=sys.stderr)

            finally:
                print('closing socket', file=sys.stderr)
                sock.close()
            yield 1 


tcps = TCPServer()
tcps.background()
time.sleep(1)

tcpc = TCPClient("127.0.0.1", 12345, message=b"This is the message to be sent, it will be echoed back")
tcpc.background()

while True:
    time.sleep(1)
