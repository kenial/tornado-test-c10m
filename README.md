tornado-test-c10m
=================
Simple echo server &amp; client that supports TCP / WebSocket. Using Tornado. Supposed to run on one host.


Goals
-----
Many articles about setting up C10M (10,000,000 concurrent connections) server out there, and you can find out code samples, usually supporting WebSocket. This sample code is backed by Tornado and supports TCP / WebSocket.

Basically, server in this code is just an echo server, but there is some workaround for C10M.

How to run
----------
Do tuning host for C10M: It varies which OS you're using. Just google "C10M performance tuning *{your os name}*," then you got tons of articles.

Install Tornado.

	pip install tornado

Open two terminals, run server.py in one.

	(fp)Kenials-MacBook-Pro:tornado-test-c10m kenial$ python server.py
	[W 141119 02:56:13 server:62]
	[W 141119 02:56:13 server:63] Server: Test C1M on Tornado (Press Q to quit)
	[W 141119 02:56:13 server:64] ---------------------------------------------
	[W 141119 02:56:13 server:46] 0 TCP conns, 0.00 reqs/s, 0 bytes/s
	[W 141119 02:56:13 server:47] 0 WS conns, 0.00 reqs/s, 0 bytes/s

Run tcp_client.py or ws_client.py in other one.

	(fp)Kenials-MacBook-Pro:tornado-test-c10m kenial$ python tcp_client.py
	[W 141119 02:56:54 tcp_client:153] TCP Client: Test C1M on Tornado
	[W 141119 02:56:54 tcp_client:154] -------------------------------
	[W 141119 02:56:54 tcp_client:155]
	[W 141119 02:56:54 tcp_client:72] Concurrent conns: 0
	[W 141119 02:56:54 tcp_client:73] (C)reate TCP connections
	[W 141119 02:56:54 tcp_client:74] (S)end messages to opened connections
	[W 141119 02:56:54 tcp_client:75] Create TCP connections and send (B)ulk messages
	[W 141119 02:56:54 tcp_client:76] (R)emove All connections
	[W 141119 02:56:54 tcp_client:77] (Q)uit
	c
	[W 141119 02:57:04 tcp_client:83] How many connections:
	1000
	[W 141119 02:57:07 tcp_client:142] elapsed: 0.013293

Working notes
-------------
http://keniallee.blogspot.com/2014/11/testing-c10m-on-host-with-tornado.html

(If you're a Korean, read this: http://kenial.tistory.com/917)
