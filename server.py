"""
test-c10m-tornado: server.py

Simple echo server that acccepts TCP and WS connections.
This codes are intended to handle 10M concurrent connections "in one host."
"""
# Written by Kenial Lee (keniallee@gmail.com)

import logging
import thread
import sys
import time

import tornado.ioloop
from tornado.options import define, options

# Assuming that 50K ephemeral ports available, 50,000 * 200 = 10,000,000 (10M)
PORT_COUNT = 200

# For displaying throughput
processed_requests, processed_bytes = 0, 0
last_display_time = time.time()

# Ports for TCP and WS (8001~8200, 8501~8700)
define("tcpport", default=8001, help="TCP port", type=int)
define("wsport", default=8501, help="WebSocket port", type=int)
options.parse_command_line(sys.argv)

from socket_connection import WebSocketApp, TCPSockServer
tcpserver = None
webapp = None

# Just notifies reloading
def reload_main():
    logging.warn("")
    logging.warn("Reload...")

def display_stats():
    global tcpserver
    global webapp
    while True:
        rps_tcp, bps_tcp = tcpserver.get_process_stats()
        rps_ws, bps_ws = webapp.get_process_stats()
        logging.warn("%d TCP conns, %.2f reqs/s, %d bytes/s", len(tcpserver.connections), rps_tcp, bps_tcp)
        logging.warn("%d WS conns, %.2f reqs/s, %d bytes/s", len(webapp.connections), rps_ws, bps_ws)
        time.sleep(3)

def console_io_loop():
    while True:
        line = sys.stdin.readline().strip().lower()
        if not line:
            pass
        elif line[0] == "q":
            tornado.ioloop.IOLoop.instance().stop()
            break


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.WARN)
    logging.warn("")
    logging.warn("Server: Test C1M on Tornado (Press Q to quit)")
    logging.warn("---------------------------------------------")

    logging.info("WebSocketApp listen: {0}".format(options.wsport))
    webapp = WebSocketApp()
    for i in range(PORT_COUNT):
        webapp.listen(options.wsport + i)

    logging.info("TCPSockServer listen: {0}".format(options.tcpport))
    tcpserver = TCPSockServer()
    for i in range(PORT_COUNT):
        tcpserver.listen(options.tcpport + i)

    tornado.autoreload.add_reload_hook(reload_main)
    tornado.autoreload.start()

    thread.start_new_thread(console_io_loop, ())
    thread.start_new_thread(display_stats, ())
    tornado.ioloop.IOLoop.instance().start()
