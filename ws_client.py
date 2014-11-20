"""
test-c10m-tornado: WebSocket client
"""
# Written by Kenial Lee (keniallee@gmail.com)

import sys
import logging
import time
import thread
import socket

import tornado.websocket
import tornado.ioloop
import tornado.gen
import tornado.autoreload

from tornado.options import define, options

from config import PORT_COUNT, WS_PORT, HOST_IP

# For displaying throughput
processed_requests, processed_bytes = 0, 0
last_display_time = time.time()

define("wsport", default=WS_PORT, help="WebSocket port", type=int)
define("host", default=HOST_IP, help="Server IP", type=str)
options.parse_command_line(sys.argv)

connections = set()
conn_try_count = 0
write_try_count = 0

@tornado.gen.coroutine
def loop_websocket(ws):
    global write_try_count
    while True:
        if ws.stream.closed():
            logging.info("loop out - closed!")
            try:
                connections.remove(ws)
            except:
                pass
            break
        data = yield ws.read_message()
        write_try_count -= 1
        if data:
            logging.info("on_message (%d): " % (len(data),))

@tornado.gen.coroutine
def make_websocket_connection(host, port):
    global conn_try_count
    url = "ws://%s:%d/ws" % (host, port)
    conn_try_count += 1
    ws = yield tornado.websocket.websocket_connect(url)
    conn_try_count -= 1
    ws.stream.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    connections.add(ws)
    loop_websocket(ws)

def close_all_connections():
    while connections:
        ws = connections.pop()
        ws.close()
        time.sleep(0)

def console_io_loop():
    global conn_try_count
    while True:
        logging.warn("Concurrent conns: %d" % (len(connections), ))
        logging.warn("(C)reate WS connections")
        logging.warn("(S)end messages to opened connections")
        logging.warn("(R)emove All connections")
        logging.warn("(Q)uit")
        line = sys.stdin.readline().strip().lower()
        starting = time.time()
        if not line:
            continue
        elif line[0] == "c":
            logging.warn("How many connections: ")
            connection_count = int(sys.stdin.readline().strip())
            starting = time.time()
            host = options.host
            port = options.wsport
            for i in xrange(connection_count):
                try:
                    while conn_try_count > 100:
                        time.sleep(0.001)
                    tornado.ioloop.IOLoop.current().add_callback(
                        make_websocket_connection,
                        *(host, port + (i % PORT_COUNT))
                    )
                except:
                    logging.warn("Error occured after %dth connection." % i)
                    import traceback; traceback.print_exc();
        elif line[0] == "s":
            logging.warn("Input message length: ")
            message_length = int(sys.stdin.readline().strip())
            message = "M" * message_length
            starting = time.time()
            for i, ws in enumerate(connections):
                while write_try_count > 100:
                    time.sleep(0.001)
                tornado.ioloop.IOLoop.current().add_callback(
                    ws.write_message,
                    *(message,)
                )
            logging.warn("Sent to %d connections (%d bytes)" % (len(connections), len(connections) * len(message)))
        elif line[0] == "r":
            close_all_connections()
        elif line[0] == "q":
            tornado.ioloop.IOLoop.current().add_callback(
                close_all_connections
            )
            logging.warn("elapsed: %f" % (time.time()-starting))
            tornado.ioloop.IOLoop.instance().stop()
            break
        logging.warn("elapsed: %f" % (time.time()-starting))

def reload_main():
    logging.warn("")
    logging.warn("Reload...")
    logging.warn("")


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.WARN)
    logging.warn("WS Client: Test C1M on Tornado")
    logging.warn("------------------------------")
    logging.warn("")

    tornado.autoreload.add_reload_hook(reload_main)
    tornado.autoreload.start()

    thread.start_new_thread(console_io_loop, ())
    tornado.ioloop.IOLoop.instance().start()
