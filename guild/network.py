#!/usr/bin/python
# -*- coding: utf-8 -*-
"""\
"""


import select
import socket
import sys
import errno
import random
import time
import os
import logging

import guild
from guild.actor import *

debug = False

for actor_class_name in ["Selector", "TCPServer", "RawConnectionHandler","EchoServer"]:
    logger = logging.getLogger(__name__ +"." + actor_class_name)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def Print(*args):
    if debug:
        sys.stderr.write(" ".join([str(x) for x in args]))
        sys.stderr.write("\n")
        sys.stderr.flush()


#NOTE: Initially the aim here is convenience. Things could be improved.
class Selector(Actor):
    """
    Purpose:
        Handle notifications regarding activity on non-blocking sockets.

    Constructor call:
        Selector()          # No arguments

    Primary Thread behaviour:
        * Wait for activity on any of the sockets
            * Notify socket handler via appropriate callback
            * Remove caller - (Prevents mutiple notifications for same event)

    Shutdown Behaviour:
        Just exits.
        Does not attempt to shutdown anything else, or notify anything else

    Actor methods:
        selector.add_reader(sock, read_ready_notification_callback)
        selector.add_writer(sock, write_ready_notification_callback)
        selector.add_exceptional(sock, exceptional_notification_callback)

    Actor Functions:
        These are actor functions to prevent a race hazard.

        selector.remove_reader(sock)
        selector.remove_writer(sock)
        selector.remove_exceptional(sock)

        You may want to do these when your protocol shuts down.
        These are safe to call if the selector is not managing your socket

    Config options:
        Selector.SELECT_TIMEOUT = 0.05 (Effectively responsiveness to actor
                                        methods/functions is dictated by this)
    """
    SELECT_TIMEOUT = 0.05
    def __init__(self):
        super(Selector,self).__init__()
        self.readers = {}
        self.writers = {}
        self.exceptionals = {}

    @actor_function
    def remove_reader(self, sock):
        try:
            del self.readers[sock]
        except KeyError:
            Print("WARNING - attempt to remove same socket twice", sock)

    @actor_function
    def remove_writer(self, sock):
        try:
            del self.writers[sock]
        except KeyError:
            Print("WARNING - attempt to remove same socket twice", sock)

    @actor_function
    def remove_exceptional(self, sock):
        try:
            del self.exceptionals[sock]
        except KeyError:
            Print("WARNING - attempt to remove same socket twice", sock)

    @actor_method
    def add_reader(self, sock, callback):
        self.readers[sock] = callback

    @actor_method
    def add_writer(self, sock, callback):
        self.writers[sock] = callback

    @actor_method
    def add_exceptional(self, sock, callback):
        self.exceptionals[sock] = callback

    def main(self):
        self.readers_busy = {}

        while True:
            yield 1
            # NOTE: This could be improved.
            readers = self.readers.keys()
            writers = self.writers.keys()
            exceptionals = self.exceptionals.keys()
            readers_ready, writers_ready, exceptionals_ready = select.select(readers, writers, exceptionals, self.SELECT_TIMEOUT)
            for sock in readers_ready:
                callback = self.readers[sock]
                del self.readers[sock]  # Always delete after notifying - means this no longer requires an actor function
                callback()
                yield 1
            for sock in writers_ready:
                callback = self.writers[sock]
                del self.writers[sock]  # Always delete after notifying - means this no longer requires an actor function
                callback()
                yield 1
            for sock in exceptionals_ready :
                callback = self.exceptionals[sock]
                del self.exceptionals[sock]  # Always delete after notifying - means this no longer requires an actor function
                callback()
                yield 1
            yield 1

    def onStop(self):
        # Print("Selector STOPPING")
        pass

# FIXME: This should really be a service

selector = None

def get_selector():
    global selector
    if selector:
        return selector
    selector = Selector()
    start(selector)
    return selector


def stop_selector():
    stop(selector)


def waitfor_selector():
    wait_for(selector)


#
# Kinda similar to the old Kamaelia.Internet.ConnectedSocketAdapter
#
class RawConnectionHandler(Actor):
    """
    Purpose:

        Directly manage talking an active socket

    Constructor call:

        RawConnectionHandler(client_sock, addr, on_exit_cb [, selector] )

        client_sock - a socket that has "someone" connected to the other end.
        addr - address connection info
        on_exit_cb - callback to call when this handler stops
        selector - selector to use [optional]

        Note for a server:

            client_sock, addr = server_socket.accept()

    Primary Thread behaviour:

        At start up, asks the selector to notify it if there's data on
        the input, and is then event driven by actor methods and the
        public bindable API

    Shutdown Behaviour:

        Notifies the server (our creator) that the raw connection has exitted.
        It does this as follows:

            self.on_exit_cb(self)

    Actor methods:

        raw_connection_handler.read_from_socket()
        raw_connection_handler.handle_socket_read_ready()

            NOTE: Perhaps should be called "read_from_socket"
            NOTE: Perhaps should be called "handle_socket_read_ready"

            NOTE: This is really about the socket being ready for reading

                - Or perhaps split into two names?
                - One that handles the message, one that does the work
                - That would be nice, and probably make most sense

            Triggered by the selector when there is data on the socket for
            us to handle. Effectively does this:

                data = self.client_sock.recv(SIZE)
                if success:
                    # Emit via "from_connection" :
                    self.from_connection(data)
                    Add ourselves to the selector again
                if retryable failure:
                    Add ourselves to the selector again
                if fatal failure:
                    Shutdown / Stop

        raw_connection_handler.write_to_socket()
        raw_connection_handler.handle_socket_write_ready()

            NOTE: The reason the client doesn't bind to this is because this
            is really about the socket being ready to send.

                - Or perhaps split into two names?
                - One that handles the message, one that does the work
                - That would be nice, and probably make most sense

            Triggered whenever there is data to send, specifically::
                - when there's an external API call for "to_connection"
                - when we've tried sending but could not empty the buffer

            Logic:  (NOTE: isn't actually this but probably should be(!))
                If outbuffer is empty:
                    return

                while chunks in self.outbuffer:
                    length_sent = self.client_sock.send(chunk)
                    if fatal error:
                        shutdown/stop
                    if retryable error:
                        requeue (at start) the chunk (or part of chunk) to send
                        break out of Loop

                if outbuffer is not empty: # This should be the case
                    Add ourselves to the selector again to resend

    Other methods:

        self.add_reader_to_selector()
            Used internally to ask the selector to nofify the RCH when there is data to
            be read

        self.add_writer_to_selector()
            selector.add_writer(self.client_sock, self.data_to_client)

    External BINDable API:

        raw_connection_handler.from_connection(chunk)  [ intended to late bound FROM ]

            Called whenever there is any data from the connection.
            If unbound, then the data is lost.

        raw_connection_handler.to_connection(chunk)    [ intended to late bound TO ]

            When called, data is buffer in an outbuffer
            The selector is then asked to notify us when the socket is ready to write to

        given rch ISA RawConnectionHandler (from somewhere)
              ph  ISA protocol_handler

        Bind data from the connection to our protocol handler

            rch.bind("from_connection", ph, "from_connection")

        Bind data from the protocol handler to our connection

            ph.bind("to_connection", rch, "to_connection")

    """
    def __init__(self, client_sock, addr, on_exit_cb, selector=None):
        super(RawConnectionHandler, self).__init__()
        self.client_sock = client_sock
        self.addr = addr
        self.selector = selector
        self.buffer = []            # FIXME: TO BE DELETED 
        self.outbuffer = []
        self.on_exit_cb = on_exit_cb
        self.send_open = True
        self.recv_open = True

    def onStop(self):
        # Print("Notify the Server that Raw Connection has exitted.")
        cb = self.on_exit_cb
        cb(self)

    @actor_method
    def handle_socket_read_ready(self):
        self.read_from_socket()

    def read_from_socket(self):
        try:
            data = self.client_sock.recv(100)
            while len(data) != 0:              # while data
                # Otherwise OK - pass data on
                self.from_connection(data)
                data = self.client_sock.recv(100)
        except socket.error as e:
            if e.errno == errno.EAGAIN:
                # FAIL, wait again
                self.add_reader_to_selector()
                return
            if e.errno == errno.EWOULDBLOCK:
                # FAIL, wait again
                self.add_reader_to_selector()
                return

        if len(data) == 0:
            Print("CLIENT HAS GONE AWAY")
            Print("Exitting")
            self.client_sock.close()
            self.client_sock = None
            self.stop()
            return

        # All data passed on, or error, or disconnect, so done
        # Re-add self to selector to say we've read all the data

        self.add_reader_to_selector()

    def add_reader_to_selector(self):
        selector.add_reader(self.client_sock, self.handle_socket_read_ready)

    def add_writer_to_selector(self):
        selector.add_writer(self.client_sock, self.handle_socket_write_ready)

    def process_start(self):
        if self.selector is None:
            self.selector = get_selector()
        self.add_reader_to_selector()

    @actor_method
    def handle_socket_write_ready(self):
        self.write_to_socket()

    def write_to_socket(self):
        if len(self.outbuffer) == 0: # Shouldn't be able to get here, but there are odd edge cases
            return

        while len(self.outbuffer) > 0:
            chunk = self.outbuffer.pop(0)
            Print("Chunk to send", len(chunk))
            try:
                bytes_sent = self.client_sock.send(chunk)
            except socket.error as e:   # e.errno ; e.errmsg:
                if e.errno == errno.EAGAIN:
                    # FAIL, wait again
                    x.insert(0, chunk)
                    self.add_writer_to_selector()
                    return

                if e.errno == errno.EWOULDBLOCK:
                    # FAIL, wait again
                    x.insert(0, chunk)
                    self.add_writer_to_selector()
                    return
                Print("Unexpected error sending. Disconnect client")
                self.stop()

            if len(chunk) == bytes_sent:
                Print("Chunk send success")
                # if len(self.outbuffer) > 0:  # Guaranteed by the loop we're in
                #     self.add_writer_to_selector()
                # return
            else:
                Print("Chunk send almost success, actually sent", bytes_sent, "vs",  len(chunk))
                # Did not manage to send all the data from this chunk. Try again in a moment with the rest
                still_to_send = chunk[bytes_sent:]
                x.insert(0, chunk)
                self.add_writer_to_selector()

        Print("All chunks sent")


    # Public Interface
    @late_bind_safe
    def from_connection(self, chunk):
        pass

    # Public Interface
    @actor_method
    def to_connection(self, chunk):
        Print("Data to connection", repr(chunk))
        self.outbuffer.append(chunk)
        self.add_writer_to_selector()


# Kinda similar to Kamaelia.Internet.TCPServer
class TCPServer(Actor):

    maxlisten = 5
    socketOptions = [socket.SOL_SOCKET, socket.SO_REUSEADDR, 1] 
    HOST=''
    PORT = 54321

    def __init__(self, selector=None, nonblocking=False,
                       host=None, port=None, socketOptions=None, maxlisten=None):
        super(TCPServer, self).__init__()
        self.handlers = []
        self.nonblocking = nonblocking
        self.selector = selector
        self.server_socket = None

        # Local overrides
        if host:
            self.HOST = host
        if port:
            self.PORT = port
        if socketOptions:
            self.socketOptions = socketOptions
        if maxlisten:
            self.maxlisten = maxlisten

    def add_reader_to_selector(self):
        selector.add_reader(self.server_socket, self.new_connection)

    def process_start(self):
        if self.selector is None:
            self.selector = get_selector()

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.socketOptions:
            self.server_socket.setsockopt(*self.socketOptions)

        if self.nonblocking:
            self.server_socket.setblocking(0)   # For the moment, do blocking

        self.server_socket.bind( (self.HOST, self.PORT) )
        self.server_socket.listen(self.maxlisten)

        self.add_reader_to_selector()
        Print("TCP LISTENING", (self.HOST, self.PORT))

    def server_stats(self):
        Print("Number of active connections", len(self.handlers))



    # NOTE: This is an actor function because otherwise the selector implementation needs to be more complex.
    #       in particular, the select call will repeatedly exit until we accept the connection
    @actor_method
    def new_connection(self):
        client_sock, addr = self.server_socket.accept()                         # Could fail

        client_sock.setblocking(0)   # For the moment, do blocking
        c = RawConnectionHandler(client_sock, addr, self.on_client_disconnect)
        self.handlers.append(c)
        self.add_reader_to_selector()  # Handled connection, so re-add us

        #

        self.wire_up_new_connection(c)

        self.server_stats()

    @actor_method
    def on_client_disconnect(self, handler):
        self.notify_protocol_on_client_disconnect(handler)
        if handler in self.handlers:
            i = self.handlers.index(handler)
            del self.handlers[i]
        self.server_stats()

    def onStop(self):
        self.server_stats()
        stop(*self.handlers)
        wait_for(*self.handlers)

    # Public Interface
    @late_bind_safe
    def wire_up_new_connection(self, connection):
        Print("Wire up new connection", connection)
        pass

    @late_bind_safe
    def notify_protocol_on_client_disconnect(self, connection):
        Print("Notify protocol on client disconnect", connection)
        pass


class ServerCore(Actor):
    server_options = { "host" : None,
                       "port" : None,
                       "socketOptions" : None,
                       "maxlisten" : None }
    base_server = TCPServer
    protocol_class = None
    def __init__(self, server_options=None, protocol_class=None, base_server=None):
        super(ServerCore, self).__init__()
        self.active_connections = {}
        self.tcpserver = None
        if server_options is not None:
            options = {}
            options.update(self.server_options)
            options.update(server_options)
            self.server_options = options

        if protocol_class is not None:
            self.protocol_class = protocol_class
        if base_server is not None:
            self.base_server = base_server

    @actor_method
    def new_connection(self, raw_connection_handler):

        rch = raw_connection_handler
        protocol_handler = (self.protocol_class)()

        rch.bind("from_connection", protocol_handler , "input")
        protocol_handler.bind("output", rch, "to_connection")

        self.active_connections[rch] = protocol_handler

        protocol_handler.start()
        rch.start()

    @actor_method
    def disconnection(self, raw_connection_handler):

        rch = raw_connection_handler

        rch.stop()
        protocol_handler = self.active_connections[rch]
        del self.active_connections[rch]

        protocol_handler.stop()

    def process_start(self):
        self.tcpserver = (self.base_server)(**self.server_options)

        self.tcpserver.bind("wire_up_new_connection",               self, "new_connection")
        self.tcpserver.bind("notify_protocol_on_client_disconnect", self, "disconnection")

        start(self.tcpserver)

    def onStop(self):
        Print("Next: STOP TCP SERVER", self.tcpserver)
        stop(self.tcpserver)

        Print("Next: WAITFOR TCP SERVER", self.tcpserver)
        wait_for(self.tcpserver)


class MulticastTransceiver(Actor):
    def __init__(self):
        # Multicast address and port we join
        self.local_addr = "224.0.0.123"
        self.local_port = 5040

        # Multicast address and port we send to (may be same)
        self.remote_addr = "224.0.0.123"
        self.remote_port = 5040

        self.tosend = []  # Not Yet...
        self.sock = None
        super(MulticastTransceiver, self).__init__()

    def process_start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                             socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Receive from server on this port
        sock.bind((self.local_addr, self.local_port))

        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)

        status = sock.setsockopt(socket.IPPROTO_IP,
                                 socket.IP_ADD_MEMBERSHIP,
                                 socket.inet_aton(self.remote_addr) + socket.inet_aton("0.0.0.0"))

        sock.setblocking(0)

        self.sock = sock   # Now effectively signifes ready...

    @process_method
    def process(self):
        try:
            data, addr = self.sock.recvfrom(16384)
        except socket.error:
            e = sys.exc_info()[1]
        else:
            message = (addr, data)
            self.output(message, time.time())

        remote_socket_spec = (self.remote_addr, self.remote_port)
        while len(self.tosend) > 0:
            try:
                l = self.sock.sendto(self.tosend[0], remote_socket_spec)
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
