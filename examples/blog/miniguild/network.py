#!/usr/bin/python
"""mini-guild Example

Simple network example

"""

import socket
import sys

from miniguild import Scheduler, Actor

class ProtocolHandler:
        def __init__(self, connection, client_address):
            self.connection = connection
            self.client_address = client_address
        def main(self):
            try:
                print('connection from', self.client_address, file=sys.stderr)
                # Receive the data in small chunks and retransmit it
                while True:
                    data = self.connection.recv(16)
                    print('received "%s"' % data, file=sys.stderr)
                    if data:
                        print('sending data back to the client', file=sys.stderr)
                        self.connection.sendall(data)
                    else:
                        print('no more data from', self.client_address, file=sys.stderr)
                        break
                    
            finally:
                # Clean up the connection
                self.connection.close()
    

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
            ph = ProtocolHandler(connection, client_address)
            ph.main()



tcps = TCPServer()
tcps.main()
