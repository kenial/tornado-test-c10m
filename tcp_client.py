"""
test-c10m-tornado: TCP client
"""
# Written by Kenial Lee (keniallee@gmail.com)

import sys
import socket
import logging
import time
import thread

import tornado.ioloop
import tornado.iostream
import tornado.gen
import tornado.autoreload

from tornado.options import define, options

# Assuming that 50K ephemeral ports available, 50,000 * 200 = 10,000,000 (10M)
PORT_COUNT = 200

# For displaying throughput
processed_requests, processed_bytes = 0, 0
last_display_time = time.time()

# IP, Ports for TCP
define("tcpport", default=8001, help="TCP port", type=int)
define("host", default="127.0.0.1", help="Server IP", type=str)
options.parse_command_line(sys.argv)

connections = set()
conn_count = 0
write_count = 0

def on_read(data):
    if data:
        logging.info("on_read (%d bytes): " % (len(data),))

def on_write():
    global write_count
    logging.info("on_write")
    write_count -= 1

def on_close(*kargs, **kwargs):
    logging.info("on_close kargs: %s kwargs: %s" % (kargs, kwargs))

def pass_stream(stream):
    def on_connect(*kargs, **kwargs):
        global conn_count
        logging.info("on_connect kargs: %s kwargs: %s" % (kargs, kwargs))
        if not stream.closed():
            stream.set_close_callback(on_close)
            stream.read_until_close(on_read, on_read)
            connections.add(stream)
        conn_count -= 1
    return on_connect

def make_connection(host, port):
    global conn_count
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    s.settimeout(0)
    stream = tornado.iostream.IOStream(s)
    stream.set_nodelay(True)
    conn_count += 1
    stream.connect((host, port), callback=pass_stream(stream))

def close_all_connections():
    while connections:
        stream = connections.pop()
        tornado.ioloop.IOLoop.current().add_callback(
            stream.close
        )

def console_io_loop():
    global write_count
    while True:
        logging.warn("Concurrent conns: %d" % (len(connections), ))
        logging.warn("(C)reate TCP connections")
        logging.warn("(S)end messages to opened connections")
        logging.warn("(R)emove All connections")
        logging.warn("(Q)uit")
        line = sys.stdin.readline().strip().lower()
        starting = time.time()
        if not line:
            continue
        elif line == "c":
            logging.warn("How many connections: ")
            connection_count = int(sys.stdin.readline().strip())
            starting = time.time()
            try:
                i = 0
                port = options.tcpport
                host = options.host
                for i in xrange(connection_count):
                    while conn_count > 100:
                        time.sleep(0.001)
                    tornado.ioloop.IOLoop.current().add_callback(
                        make_connection,
                        *(host, port + (i % PORT_COUNT))
                    )
            except:
                logging.warn("Error occured after %dth connection." % i)
                import traceback; traceback.print_exc();
        elif line == "s":
            logging.warn("Input message length: ")
            message_length = int(sys.stdin.readline().strip())
            message = "M" * message_length
            starting = time.time()
            for i, stream in enumerate(connections):
                while write_count > 100:
                    time.sleep(0.001)
                tornado.ioloop.IOLoop.current().add_callback(
                    stream.write, *(message,)
                )
                write_count += 1
            logging.warn("Sent to %d connections (%d bytes)" % (len(connections), len(connections) * len(message)))
        elif line == "r":
            close_all_connections()
        elif line == "q":
            close_all_connections()
            logging.warn("elapsed: %f" % (time.time()-starting))
            break
        logging.warn("elapsed: %f" % (time.time()-starting))
    tornado.ioloop.IOLoop.instance().stop()

def reload_main():
    logging.warn("")
    logging.warn("Reload...")
    logging.warn("")


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.WARN)
    logging.warn("TCP Client: Test C1M on Tornado")
    logging.warn("-------------------------------")
    logging.warn("")

    tornado.autoreload.add_reload_hook(reload_main)
    tornado.autoreload.start()

    thread.start_new_thread(console_io_loop, ())
    tornado.ioloop.IOLoop.instance().start()