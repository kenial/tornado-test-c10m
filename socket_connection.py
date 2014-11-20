"""
test-c10m-tornado: socket_connection.py

Server and connection class for TCP / WebSocket. If you wanna make your own
server logic, take and extend these freely.
"""
# Written by Kenial Lee (keniallee@gmail.com)

import time
import logging

import tornado
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.tcpserver
import tornado.autoreload


# WebSocket stuff
class WebSocketApp(tornado.web.Application):
    """Tornado WebSocket application.
    """

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
    """Provides ECHO logic.
    """

    def __init__(self, application, request, **kwargs):
        logging.info("WebSocketHandler:__init__ from %s", request.connection.context.address)
        super(self.__class__, self).__init__(application, request, **kwargs)

    def allow_draft76(self):    # for iOS 5.0 Safari
        return True

    def open(self):
        logging.info("WebSocketHandler:open")
        self.set_nodelay(True)
        self.application.handle_open(self)

    def close(self):
        logging.info("WebSocketHandler:close")
        super(self.__class__, self).close()

    def on_close(self):
        logging.info("WebSocketHandler:on_close")
        self.application.handle_close(self)

    def on_message(self, data):
        logging.info("WebSocketHandler:on_message (%d bytes)" % len(data))
        self.application.add_process_stats(len(data))
        # just ECHO
        self.write_message(data)

    def write_message(self, data):
        logging.info("WebSocketHandler:write_message (%d bytes)" % len(data))
        try:
            if not self.stream.closed():
                super(self.__class__, self).write_message(data)
                self.application.add_process_stats(len(data))
        except tornado.iostream.StreamClosedError, ex:
            logging.error("write_message failed. close again...", exc_info=True)
            self.close()
            raise ex



# TCP socket stuff
class TCPSockServer(tornado.tcpserver.TCPServer):
    """Tornado TCP socket server.
    """

    def __init__(self, io_loop=None, ssl_options=None, **kwargs):
        logging.info('TCPSockServer.__init__')
        super(self.__class__, self).__init__(io_loop=io_loop, ssl_options=ssl_options, **kwargs)
        self.connections = set()
        self.last_stats_time = time.time()
        self.processed_requests = 0
        self.processed_bytes = 0

    def handle_stream(self, stream, address):
        logging.info("TCPSockServer:handle_stream %s", address)
        stream.set_nodelay(True)
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
    """Provides ECHO Logic.
    """

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
        if len(data) > 0:
            logging.info('TCPSockConnection (%d):_on_read_finish (%d bytes)', self.order, len(data))
            self.sock_server.add_process_stats(len(data))
        else:
            logging.info('TCPSockConnection (%d):_on_read_finish but zero length data', self.order)

    def _on_read_line(self, data):
        logging.info('TCPSockConnection (%d):_on_read_line', self.order)
        pass

    def _on_write_complete(self):
        logging.info('TCPSockConnection (%d):_on_write_complete', self.order)
        pass

    def _on_close(self):
        logging.info('TCPSockConnection (%d):_on_close', self.order)
        self.sock_server.handle_close(self)
