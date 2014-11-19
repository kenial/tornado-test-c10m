# Copyright 2014, Kenial Lee

import time
import logging

#############################
# setting Tornado environment
import tornado
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.tcpserver
import tornado.autoreload

#####################################################
# WebSocket stuff
class WebSocketApp(tornado.web.Application):
    """Websocket application for Fountain connection"""
    def __init__(self):
        logging.info('WebSocketApp __init__')
        handlers = [
            (r'/ws', WebSocketHandler),
        ]
        settings = {
        }
        tornado.web.Application.__init__(self, handlers, **settings)
        self.connections = set()
        self.last_stats_time = time.time()
        self.processed_requests = 0
        self.processed_bytes = 0

    def handle_open(self, connection):
        self.connections.add(connection)

    def handle_close(self, connection):
        self.connections.remove(connection)

    def add_process_stats(self, bytes):
        self.processed_requests += 1
        self.processed_bytes += bytes

    def get_process_stats(self):
        now = time.time()
        elapsed_time = now - self.last_stats_time
        self.last_stats_time = now
        rps = self.processed_requests / elapsed_time
        bps = self.processed_bytes / elapsed_time
        self.processed_requests = 0
        self.processed_bytes = 0
        return rps, bps

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    """Handler for Fountain connection"""
    def __init__(self, application, request, **kwargs):
        logging.info("WebSocketHandler:__init__ from %s", request.connection.context.address)
        super(self.__class__, self).__init__(application, request, **kwargs)

    def allow_draft76(self):    # for iOS 5.0 Safari
        return True

    # called on open!
    def open(self):
        logging.info("WebSocketHandler:open")
        self.set_nodelay(True)  # no delay for small messages
        self.application.handle_open(self)

    # already defined on WebSocketHandler
    def close(self):
        logging.info("WebSocketHandler:close")
        super(self.__class__, self).close()

    def on_close(self):
        logging.info("WebSocketHandler:on_close")
        self.application.handle_close(self)

    def on_message(self, data):
        logging.info("WebSocketHandler:on_message (%d bytes)" % len(data))
        self.application.add_process_stats(len(data))
        self.write_message(data)    # ECHO

    def write_message(self, data):
        logging.info("WebSocketHandler:write_message (%d bytes)" % len(data))
        try:
            if not self.stream.closed():
                tornado.websocket.WebSocketHandler.write_message(self, data)
                self.application.add_process_stats(len(data))
        except tornado.iostream.StreamClosedError, ex:
            logging.error("write_message failed. close again...", exc_info=True)
            self.close()
            raise ex


##############################################################
# TCP socket stuff
class TCPSockServer(tornado.tcpserver.TCPServer):
    def __init__(self, io_loop=None, ssl_options=None, **kwargs):
        logging.info('TCPSockServer.__init__')
        tornado.tcpserver.TCPServer.__init__(self, io_loop=io_loop, ssl_options=ssl_options, **kwargs)
        self.connections = set()
        self.last_stats_time = time.time()
        self.processed_requests = 0
        self.processed_bytes = 0

    def handle_stream(self, stream, address):
        logging.info("TCPSockServer:handle_stream %s", address)
        connection = TCPSockConnection(stream, address, self)
        connection.order = len(self.connections)
        self.connections.add(connection)

    def handle_close(self, connection):
        self.connections.remove(connection)

    def add_process_stats(self, bytes):
        self.processed_requests += 1
        self.processed_bytes += bytes

    def get_process_stats(self):
        now = time.time()
        elapsed_time = now - self.last_stats_time
        self.last_stats_time = now
        rps = self.processed_requests / elapsed_time
        bps = self.processed_bytes / elapsed_time
        self.processed_requests = 0
        self.processed_bytes = 0
        return rps, bps


class TCPSockConnection(object):
    def __init__(self, stream, address_from, sock_server):
        logging.info('TCPSockConnection.__init__ from %s', address_from)
        self.sock_server = sock_server
        self.stream = stream
        self.stream.set_close_callback(self._on_close)
        self.stream.read_until_close(self._on_read_finish, streaming_callback=self._on_read)

    def close(self):
        if not self.stream.closed():
            self.stream.close()

    def write_message(self, data):
        logging.info("TCPSockConnection (%d):write_message (%d)", self.order, len(data))
        try:
            message_to_send = tornado.escape.native_str(data)
            if not self.stream.closed():
                self.stream.write(message_to_send, self._on_write_complete)
                self.sock_server.add_process_stats(len(data))
        except tornado.iostream.StreamClosedError, ex:
            logging.error("write_message failed. close again...", exc_info=True)
            self.close()
            raise ex

    def _on_read(self, data):
        if len(data) > 0:
            logging.info('TCPSockConnection (%d):_on_read (%d bytes)', self.order, len(data))
            self.write_message(data)    # ECHO
            self.sock_server.add_process_stats(len(data))
        else:
            logging.info('TCPSockConnection (%d):_on_read but zero length data', self.order)

    def _on_read_finish(self, data):
        # if data is remaining, process it
        if len(data) > 0:
            logging.info('TCPSockConnection (%d):_on_read_finish (%d bytes)', self.order, len(data))
        else:
            logging.info('TCPSockConnection (%d):_on_read_finish but zero length data', self.order)

    def _on_read_line(self, data):
        logging.info('TCPSockConnection (%d):_on_read_line', self.order)
        pass
        # logging.info('TCPSockConnection (%d):_on_read_line read a new line from %s', self.address)
        # MessageHub.shared().process_json_string(self, data)

    def _on_write_complete(self):
        logging.info('TCPSockConnection (%d):_on_write_complete', self.order)
        pass

        # logging.info('wrote a line to %s', self.address)
        # if not self.stream.reading():
        #     self.stream.read_until('\n', self._on_read_line)

    def _on_close(self):
        logging.info('TCPSockConnection (%d):_on_close', self.order)
        self.sock_server.handle_close(self)
